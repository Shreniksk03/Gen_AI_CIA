import json
import logging
import os
import random
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import joblib
import numpy as np
import pandas as pd
import shap
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import Client

# Ensure both backend directory and parent directory are on sys.path
backend_dir = Path(__file__).resolve().parent
parent_dir = backend_dir.parent
for d in [str(backend_dir), str(parent_dir)]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    from backend.config import settings
    from backend.models.schemas import (
        AnalyticsResponse,
        FeatureImpact,
        HealthResponse,
        ModelInfoResponse,
        PaginatedTransactionsResponse,
        PredictionResponse,
        ReviewUpdateRequest,
        TransactionPayload,
        TransactionRecord,
    )
    from backend.services.db_service import (
        calculate_analytics,
        check_database_connectivity,
        ensure_uuid,
        get_supabase_client,
        get_transaction_by_id,
        persist_transaction,
        query_transactions,
        update_transaction_review,
    )
    from backend.services.shap_service import compute_shap_explanations
except ImportError:
    from config import settings
    from models.schemas import (
        AnalyticsResponse,
        FeatureImpact,
        HealthResponse,
        ModelInfoResponse,
        PaginatedTransactionsResponse,
        PredictionResponse,
        ReviewUpdateRequest,
        TransactionPayload,
        TransactionRecord,
    )
    from services.db_service import (
        calculate_analytics,
        check_database_connectivity,
        ensure_uuid,
        get_supabase_client,
        get_transaction_by_id,
        persist_transaction,
        query_transactions,
        update_transaction_review,
    )
    from services.shap_service import compute_shap_explanations

# -----------------------------------------------------------------------------
# 1. Logging & Environment Setup
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fraud_backend")

# Explicitly load .env from possible locations
for env_path in [
    Path(".env"),
    Path("backend/.env"),
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]:
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from: {env_path.resolve()}")
        break
else:
    load_dotenv(override=True)

SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL") or settings.SUPABASE_URL
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY") or settings.SUPABASE_KEY
SUPABASE_SERVICE_ROLE_KEY: Optional[str] = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or settings.SUPABASE_SERVICE_ROLE_KEY
)

# -----------------------------------------------------------------------------
# 2. Global Machine Learning Assets & Simulation Cache
# -----------------------------------------------------------------------------
fraud_model: Any = None
scaler: Any = None
preprocessing_pipeline: Any = None
model_columns: Optional[List[str]] = None
explainer: Optional[shap.TreeExplainer] = None
data_samples_cache: Dict[str, List[Dict[str, Any]]] = {"fraud": [], "legit": []}


def get_asset_path(filename: str) -> Path:
    """Locates model assets and metadata files across root and backend directories."""
    candidates = [
        Path(filename),
        Path("backend") / filename,
        Path(__file__).resolve().parent / filename,
        Path(__file__).resolve().parent.parent / filename,
        Path(__file__).resolve().parent.parent / "backend" / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p.resolve()
    return Path(__file__).resolve().parent / filename


def load_ml_assets() -> bool:
    """
    Loads fraud_model.joblib, scaler.joblib, preprocessing_pipeline.joblib,
    and model_columns.joblib into globals and initializes shap.TreeExplainer.
    """
    global fraud_model, scaler, preprocessing_pipeline, model_columns, explainer
    model_path = get_asset_path("fraud_model.joblib")
    scaler_path = get_asset_path("scaler.joblib")
    columns_path = get_asset_path("model_columns.joblib")
    pipe_path = get_asset_path("preprocessing_pipeline.joblib")

    if model_path.is_file() and scaler_path.is_file() and columns_path.is_file():
        try:
            fraud_model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            model_columns = joblib.load(columns_path)
            if pipe_path.is_file():
                try:
                    preprocessing_pipeline = joblib.load(pipe_path)
                    logger.info("Loaded full ColumnTransformer preprocessing_pipeline.joblib.")
                except Exception as pe:
                    logger.warning(f"Could not load preprocessing_pipeline.joblib: {pe}")

            explainer = shap.TreeExplainer(fraud_model)
            logger.info(
                f"Successfully loaded model assets ({len(model_columns)} features) "
                f"and initialized shap.TreeExplainer."
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load ML model assets: {e}", exc_info=True)
            return False
    else:
        logger.warning(
            f"Model assets not found at paths: {model_path}, {scaler_path}, {columns_path}."
        )
        return False


def load_dataset_samples():
    """Caches realistic dataset samples from backend/data.csv for instant simulation."""
    global data_samples_cache
    data_csv_path = get_asset_path("data.csv")
    if not data_csv_path.is_file():
        return

    try:
        df = pd.read_csv(data_csv_path, nrows=5000)
        df = df.fillna(0)
        fraud_df = df[df["is_fraud"] == 1]
        legit_df = df[df["is_fraud"] == 0]

        data_samples_cache["fraud"] = fraud_df.to_dict(orient="records")
        data_samples_cache["legit"] = legit_df.to_dict(orient="records")
        logger.info(
            f"Preloaded simulation cache: {len(data_samples_cache['fraud'])} fraud samples, "
            f"{len(data_samples_cache['legit'])} legit samples from data.csv."
        )
    except Exception as e:
        logger.warning(f"Could not preload data.csv samples: {e}")


# Initialize ML assets and simulation cache at module load
load_ml_assets()
load_dataset_samples()

# -----------------------------------------------------------------------------
# 3. Supabase Client Initialization
# -----------------------------------------------------------------------------
supabase: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    """FastAPI Dependency providing the connected Supabase client."""
    active_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or SUPABASE_SERVICE_ROLE_KEY
    active_anon_key = os.getenv("SUPABASE_KEY") or SUPABASE_KEY
    active_url = os.getenv("SUPABASE_URL") or SUPABASE_URL

    return get_supabase_client(
        supabase_url=active_url,
        supabase_key=active_anon_key,
        service_role_key=active_service_key,
    )


# -----------------------------------------------------------------------------
# 4. FastAPI Lifespan & App Setup
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: loads ML models and initializes database connectivity."""
    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"CORS Allowed Origins: {settings.cors_origins_list}")
    load_ml_assets()
    load_dataset_samples()
    get_supabase()
    yield
    logger.info("Shutting down Fraud Detection Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Financial Fraud Detection API with Real Trained XGBoost Model & SHAP Explanations",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# -----------------------------------------------------------------------------
# 5. Middlewares: Request ID, Structured Logging & Rate Limiting Plan
# -----------------------------------------------------------------------------
RATE_LIMIT_BUCKET: Dict[str, List[float]] = {}
RATE_LIMIT_MAX_PER_MINUTE = 300


@app.middleware("http")
async def request_lifecycle_middleware(request: Request, call_next):
    """
    Attaches unique X-Request-ID, logs structured lifecycle timing,
    and applies standard token bucket rate limiting.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = datetime.now(timezone.utc)

    # Rate limiting check (allows health and documentation endpoints without restriction)
    if request.url.path not in ("/", "/health", "/docs", "/redoc", "/openapi.json"):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now_ts = start_time.timestamp()
        timestamps = [ts for ts in RATE_LIMIT_BUCKET.get(client_ip, []) if now_ts - ts < 60.0]
        if len(timestamps) >= RATE_LIMIT_MAX_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 429,
                        "message": "Rate limit exceeded: maximum 300 requests per minute.",
                        "request_id": request_id,
                        "timestamp": start_time.isoformat(),
                    }
                },
                headers={"Retry-After": "60", "X-Request-ID": request_id},
            )
        timestamps.append(now_ts)
        RATE_LIMIT_BUCKET[client_ip] = timestamps

    response = await call_next(request)

    process_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{process_time_ms:.2f}"
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({process_time_ms:.2f}ms)"
    )
    return response


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Uniform structured JSON error response."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
        headers={"X-Request-ID": request_id},
    )


# -----------------------------------------------------------------------------
# 6. API Endpoints
# -----------------------------------------------------------------------------
@app.get("/", tags=["General"])
async def root():
    """Service status and available API route endpoints."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model_loaded": fraud_model is not None,
        "model_type": type(fraud_model).__name__ if fraud_model else None,
        "client": "supabase-py",
        "docs": "/docs",
        "endpoints": {
            "predict": "POST /predict",
            "transactions": "GET /transactions",
            "transaction_detail": "GET /transactions/{id}",
            "transaction_review": "PATCH /transactions/{id}/review",
            "analytics": "GET /analytics",
            "model_metrics": "GET /model/metrics",
            "model_info": "GET /model/info",
            "sample": "GET /transactions/sample",
            "health": "GET /health",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(client: Optional[Client] = Depends(get_supabase)):
    """Verifies service health, active model status, and live database connectivity."""
    diag = check_database_connectivity(client)
    return HealthResponse(
        status="healthy" if diag["is_healthy"] else "degraded",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database_connected=diag["is_healthy"],
        database_source=diag["authoritative_source"],
        database_source_label=diag["authoritative_source_label"],
        supabase_status=diag["supabase_status"],
        sqlite_status=diag["sqlite_status"],
        sqlite_records_count=diag["sqlite_count"],
        supabase_records_count=diag["supabase_count"],
        message=diag.get("supabase_error"),
    )


@app.get(
    "/transactions/sample",
    tags=["Simulation"],
    summary="Get a realistic transaction payload sampled from actual dataset",
    description="Samples a complete 35-feature financial transaction payload from backend/data.csv.",
)
async def get_transaction_sample(
    scenario: Literal["random", "fraud", "legit"] = "random"
):
    """Returns a realistic, valid transaction payload for simulation."""
    if not data_samples_cache["legit"] and not data_samples_cache["fraud"]:
        load_dataset_samples()

    pool: List[Dict[str, Any]] = []
    if scenario == "fraud" and data_samples_cache["fraud"]:
        pool = data_samples_cache["fraud"]
    elif scenario == "legit" and data_samples_cache["legit"]:
        pool = data_samples_cache["legit"]
    else:
        use_fraud = random.random() < 0.30
        pool = (
            data_samples_cache["fraud"]
            if (use_fraud and data_samples_cache["fraud"])
            else data_samples_cache["legit"] or data_samples_cache["fraud"]
        )

    if not pool:
        return {
            "transaction_amount": round(random.uniform(25.0, 1850.0), 2),
            "merchant_category": random.choice(["Travel & Airlines", "Online Retail", "Crypto", "Electronics"]),
            "merchant_country": random.choice(["USA", "UK", "Germany", "Nigeria", "Russia"]),
            "transaction_hour": random.randint(0, 23),
            "customer_age": random.randint(21, 75),
            "account_age_days": random.randint(15, 1200),
            "credit_score": random.randint(520, 810),
            "transactions_last_24h": random.randint(1, 9),
            "distance_from_home_km": round(random.uniform(2.0, 650.0), 1),
            "international_transaction": random.choice([0, 1]),
            "card_present": random.choice([0, 1]),
            "used_chip": random.choice([0, 1]),
        }

    raw_sample = random.choice(pool).copy()

    is_fraud_label = raw_sample.pop("is_fraud", 0)
    raw_sample.pop("fraud_type", None)
    raw_sample.pop("fraud_amount_lost", None)

    category_merchants = {
        "Travel & Airlines": ["Emirates Air", "Delta Flights", "Lufthansa", "Airbnb Worldwide"],
        "Online Retail": ["Amazon Prime", "AliExpress Global", "Shopify Store", "Apple Online"],
        "Entertainment & Streaming": ["Netflix Direct", "Steam Games", "Spotify Media", "Roblox Corp"],
        "Financial Services": ["Binance P2P", "Coinbase Pro", "Revolut Transfer", "Wise FX"],
        "Grocery & Supermarket": ["Whole Foods", "Walmart Supercenter", "Tesco Express", "Carrefour"],
        "Electronics & Technology": ["Best Buy POS", "B&H Photo Video", "Newegg Tech", "Dell Direct"],
    }
    cat = raw_sample.get("merchant_category", "Online Retail")
    merchant_name = random.choice(category_merchants.get(cat, ["Apex Merchant Direct"]))

    country_cities = {
        "USA": "New York, US",
        "UK": "London, UK",
        "Germany": "Berlin, DE",
        "India": "Mumbai, IN",
        "Nigeria": "Lagos, NG",
        "UAE": "Dubai, AE",
        "Russia": "Moscow, RU",
        "Brazil": "São Paulo, BR",
    }
    country = raw_sample.get("merchant_country", "USA")
    location_name = country_cities.get(country, f"{country} Terminal")

    raw_sample["merchant"] = merchant_name
    raw_sample["location"] = location_name
    raw_sample["card_last4"] = str(random.randint(1000, 9999))
    raw_sample["ground_truth_label"] = int(is_fraud_label)

    return raw_sample


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
    summary="Evaluate transaction with trained XGBoost model and SHAP",
    description=(
        "Ingests transaction payload, transforms through exact trained preprocessing pipeline, "
        "predicts fraud probability via XGBoost, computes TreeSHAP feature attributions, and persists record."
    ),
)
async def predict_fraud(
    payload: Dict[str, Any] = Body(...),
    request: Request = None,
    client: Optional[Client] = Depends(get_supabase),
):
    """
    POST /predict
    Full-Stack Machine Learning Workflow with TreeSHAP and Calibrated Decision Threshold.
    """
    try:
        transaction_id = ensure_uuid(payload.get("transaction_id"))
        now = datetime.now(timezone.utc)

        if fraud_model is None or scaler is None or model_columns is None or explainer is None:
            if not load_ml_assets():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Machine learning model assets are not loaded.",
                )

        amount_val = float(
            payload.get("transaction_amount")
            or payload.get("amount")
            or payload.get("Amount")
            or 100.0
        )
        payload["transaction_amount"] = amount_val

        merchant = payload.get("merchant") or "Global Payment Terminal"
        location = payload.get("location") or "Secure POS Gateway"
        category = payload.get("merchant_category") or payload.get("category") or "Online Retail"
        card_last4 = str(payload.get("card_last4") or "4242")

        df_input = pd.DataFrame([payload])

        if preprocessing_pipeline is not None:
            try:
                for feat in preprocessing_pipeline.feature_names_in_:
                    if feat not in df_input.columns:
                        if feat in ("merchant_category", "merchant_country", "transaction_day_of_week",
                                    "customer_gender", "customer_state", "transaction_channel",
                                    "device_type", "browser", "email_domain"):
                            df_input[feat] = "Other"
                        else:
                            df_input[feat] = 0.0

                scaled_array = preprocessing_pipeline.transform(df_input)
            except Exception as pe:
                logger.warning(f"ColumnTransformer fallback to manual encoding: {pe}")
                scaled_array = None
        else:
            scaled_array = None

        if scaled_array is None:
            df_encoded = pd.get_dummies(df_input)
            df_reindexed = df_encoded.reindex(columns=model_columns, fill_value=0)

            if hasattr(scaler, "feature_names_in_") and len(scaler.feature_names_in_) < len(model_columns):
                num_cols_scaler = [c for c in scaler.feature_names_in_ if c in df_reindexed.columns]
                scaled_num = scaler.transform(df_reindexed[num_cols_scaler])
                rem_cols = [c for c in model_columns if c not in num_cols_scaler]
                scaled_array = np.hstack([scaled_num, df_reindexed[rem_cols].values])
            else:
                scaled_array = scaler.transform(df_reindexed)

        proba = fraud_model.predict_proba(scaled_array)
        fraud_probability = round(float(proba[0][1]), 4)

        # Optimal calibrated operational threshold at 0.35
        is_flagged = bool(fraud_probability >= 0.35)

        if fraud_probability >= 0.60:
            risk_level = "CRITICAL"
        elif fraud_probability >= 0.40:
            risk_level = "HIGH"
        elif fraud_probability >= 0.25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        shap_result = compute_shap_explanations(
            explainer=explainer,
            scaled_array=scaled_array,
            model_columns=model_columns,
            raw_payload=payload,
            top_k=5,
        )

        top_contributors: List[FeatureImpact] = [
            FeatureImpact(
                feature=item["feature"],
                display_name=item["display_name"],
                shap_value=item["shap_value"],
                feature_value=item["feature_value"],
                direction="RISK_INCREASING" if item["shap_value"] > 0 else "RISK_DECREASING",
                impact=item["impact"],
                description=item["human_readable"],
                human_readable=item["human_readable"],
            )
            for item in shap_result["top_features"]
        ]

        positive_contributions: List[FeatureImpact] = [
            FeatureImpact(
                feature=item["feature"],
                display_name=item["display_name"],
                shap_value=item["shap_value"],
                feature_value=item["feature_value"],
                direction="RISK_INCREASING",
                impact="INCREASED_RISK",
                description=item["human_readable"],
                human_readable=item["human_readable"],
            )
            for item in shap_result["positive_contributions"]
        ]

        negative_contributions: List[FeatureImpact] = [
            FeatureImpact(
                feature=item["feature"],
                display_name=item["display_name"],
                shap_value=item["shap_value"],
                feature_value=item["feature_value"],
                direction="RISK_DECREASING",
                impact="REDUCED_RISK",
                description=item["human_readable"],
                human_readable=item["human_readable"],
            )
            for item in shap_result["negative_contributions"]
        ]

        features_dict = {
            k: v for k, v in payload.items()
            if not k.startswith("_") and k not in ("merchant", "location", "card_last4")
        }

        persist_res = persist_transaction(
            client=client,
            transaction_id=transaction_id,
            amount=amount_val,
            fraud_probability=fraud_probability,
            is_flagged=is_flagged,
            risk_level=risk_level,
            shap_explanations=shap_result["top_shap_dict"],
            top_contributors=[t.model_dump() for t in top_contributors],
            summary_narrative=shap_result["summary_narrative"],
            features=features_dict,
            merchant=merchant,
            merchant_category=category,
            location=location,
            category=category,
            card_last4=card_last4,
            model_version="xgboost-tree-explainer-v2.0",
            review_status="PENDING",
            timestamp=now,
        )

        return PredictionResponse(
            transaction_id=transaction_id,
            timestamp=now,
            fraud_probability=fraud_probability,
            is_fraud=bool(fraud_probability >= 0.35),
            is_flagged=is_flagged,
            risk_level=risk_level,
            review_status="PENDING",
            base_value=shap_result["base_value"],
            shap_values=shap_result["top_shap_dict"],
            shap_explanations=shap_result["top_shap_dict"],
            top_contributors=top_contributors,
            positive_contributions=positive_contributions,
            negative_contributions=negative_contributions,
            summary_narrative=shap_result["summary_narrative"],
            model_version="xgboost-tree-explainer-v2.0",
            logged_to_database=persist_res["success"],
            database_source=persist_res["database_source"],
            database_source_label=persist_res["database_source_label"],
            supabase_persisted=persist_res["supabase_persisted"],
            sqlite_persisted=persist_res["sqlite_persisted"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction pipeline error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failure: {str(e)}",
        )


@app.get(
    "/transactions",
    tags=["Telemetry"],
    summary="Query transactions with pagination and filters",
    description=(
        "Queries persisted transactions with database-level filtering by risk_level, is_flagged, "
        "review_status, date ranges, search term, and sorting."
    ),
)
async def get_transactions(
    request: Request,
    page: Optional[int] = Query(None, ge=1, description="Page number starting at 1"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Free-text search by ID, merchant, location, card, category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk band (LOW, MEDIUM, HIGH, CRITICAL)"),
    is_flagged: Optional[bool] = Query(None, description="Filter by operational threat flag"),
    review_status: Optional[str] = Query(None, description="Filter by review status (PENDING, UNDER_REVIEW, etc.)"),
    start_date: Optional[str] = Query(None, description="Earliest transaction timestamp ISO 8601"),
    end_date: Optional[str] = Query(None, description="Latest transaction timestamp ISO 8601"),
    sort_by: str = Query("transaction_time", description="Sort column (transaction_time, amount, fraud_probability)"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort direction"),
    legacy: bool = Query(False, description="If true, returns direct list array for backward compatibility"),
    client: Optional[Client] = Depends(get_supabase),
):
    """Enhanced GET /transactions endpoint with full filtering and pagination metadata."""
    current_page = page or 1
    records, total, pages, data_source, data_source_label = query_transactions(
        client=client,
        page=current_page,
        limit=limit,
        search=search,
        risk_level=risk_level,
        is_flagged=is_flagged,
        review_status=review_status,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    if legacy:
        return records

    return PaginatedTransactionsResponse(
        items=records,
        total=total,
        page=current_page,
        limit=limit,
        pages=pages,
        data_source=data_source,
        data_source_label=data_source_label,
    )


@app.get(
    "/transactions/{transaction_id}",
    response_model=TransactionRecord,
    tags=["Telemetry"],
    summary="Get single transaction detail by ID",
    description="Returns complete details, SHAP explanations, risk scoring, and analyst review history.",
)
async def get_transaction_detail(
    transaction_id: str,
    client: Optional[Client] = Depends(get_supabase),
):
    """Retrieves single transaction by ID or raises 404."""
    record = get_transaction_by_id(client, transaction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' was not found in the database.",
        )
    return record


@app.patch(
    "/transactions/{transaction_id}/review",
    response_model=TransactionRecord,
    tags=["Analyst Review"],
    summary="Update transaction review status and audit notes",
    description="Updates review_status, records analyst notes, and appends entry to transaction_reviews audit history.",
)
async def update_review_status(
    transaction_id: str,
    update_data: ReviewUpdateRequest = Body(...),
    client: Optional[Client] = Depends(get_supabase),
):
    """Applies analyst review decision (PENDING, UNDER_REVIEW, CONFIRMED_FRAUD, LEGITIMATE, ESCALATED)."""
    updated_record, err = update_transaction_review(
        client=client,
        transaction_id=transaction_id,
        new_status=update_data.review_status,
        analyst_notes=update_data.analyst_notes,
        reviewed_by=update_data.reviewed_by,
    )

    if err:
        if "not found" in err.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    return updated_record


@app.get(
    "/analytics",
    response_model=AnalyticsResponse,
    tags=["Analytics"],
    summary="Aggregated fraud telemetry and time-series analytics",
    description="Returns aggregate counts, risk distributions, and time-series volume trends over specified window.",
)
async def get_analytics(
    time_range: Literal["24h", "7d", "30d", "90d"] = Query("7d", description="Time window for aggregation"),
    client: Optional[Client] = Depends(get_supabase),
):
    """Computes fraud analytics distinguishing predicted threats from analyst-confirmed fraud."""
    analytics_data = calculate_analytics(client=client, time_range=time_range)
    return analytics_data


@app.get(
    "/model/metrics",
    tags=["Model Governance"],
    summary="Retrieve verified ML benchmark metrics",
    description="Reads verified metrics from model_metrics.json, distinguishing validation from holdout test results.",
)
async def get_model_metrics():
    """Returns verified model benchmarks, PR-AUC, ROC-AUC, confusion matrices, and threshold curves."""
    metrics_path = get_asset_path("model_metrics.json")
    if not metrics_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metrics benchmark file model_metrics.json was not found.",
        )

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error reading model_metrics.json: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse model metrics file.",
        )


@app.get(
    "/model/info",
    response_model=ModelInfoResponse,
    tags=["Model Governance"],
    summary="Retrieve model architecture, training configuration, and risk bands",
)
async def get_model_info():
    """Returns model metadata, feature schemas, SHAP output space, and calibrated threshold configuration."""
    input_schema = [
        "transaction_amount", "merchant_category", "merchant_country", "transaction_hour",
        "transaction_day_of_week", "card_present", "customer_age", "customer_gender",
        "customer_state", "account_age_days", "credit_limit", "credit_score", "num_cards_held",
        "transactions_last_1h", "transactions_last_24h", "transactions_last_7d", "amount_last_1h",
        "amount_last_24h", "days_since_last_transaction", "distance_from_home_km",
        "distance_from_last_tx_km", "international_transaction", "high_risk_country",
        "amount_vs_avg_ratio", "used_chip", "used_pin", "transaction_channel", "device_type",
        "browser", "is_weekend", "avg_transaction_amount_30d", "std_transaction_amount_30d",
        "num_declined_last_30d", "num_chargebacks_ever", "email_domain",
    ]

    return ModelInfoResponse(
        model_name="XGBoost Financial Fraud Classifier",
        algorithm="XGBClassifier (Extreme Gradient Boosting)",
        version="2.1.0-production",
        training_date="2026-11-05T15:09:41Z",
        number_of_features=35,
        number_of_encoded_features=len(model_columns) if model_columns else 131,
        input_feature_schema=input_schema,
        preprocessing={
            "pipeline": "ColumnTransformer",
            "numerical_scaler": "StandardScaler (fitted on 26 numerical columns)",
            "categorical_encoder": "OneHotEncoder(handle_unknown='ignore') on 9 categoricals",
            "class_imbalance_technique": "Cost-sensitive scale_pos_weight = 47.66",
        },
        shap_output_space="TreeExplainer raw margin space (log-odds) with logistic sigmoid probability mapping",
        selected_threshold=0.35,
        decision_rationale=(
            "Calibrated on stratified validation partition to optimize fraud recall (74.7%) while "
            "maintaining practical analyst queue volume and peak F1 score (0.1136)."
        ),
        risk_band_configuration={
            "LOW": "p < 0.25 (Automated clearance)",
            "MEDIUM": "0.25 <= p < 0.60 (Elevated queue inspection)",
            "HIGH_CRITICAL": "p >= 0.60 (Immediate authorization freeze)",
            "investigation_flag": "is_flagged = (p >= 0.35)",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
