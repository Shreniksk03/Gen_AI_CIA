# FraudSentinel - FastAPI Backend

Production-ready financial fraud detection microservice built with **FastAPI**, **Pydantic v2**, and **Supabase PostgreSQL**. It powers real-time inference, SHAP-based model explainability, and transaction logging.

---

## Features

- **High-Performance FastAPI**: Asynchronous API with automatic OpenAPI (Swagger UI) documentation.
- **CORS Configured**: Pre-configured to accept requests from your local Next.js frontend (`http://localhost:3000`, `http://127.0.0.1:3000`).
- **`POST /predict` Endpoint**: Evaluates transactions with trained XGBoost model & StandardScaler.
- **SHAP TreeExplainer**: Extracts top 3 feature attributions explaining the model's decision in real-time.
- **Supabase Telemetry**: Asynchronous database logging into `transactions` table with pooling and fallback resilience.

---

## Directory Structure

```
backend/
├── main.py                 # FastAPI application with real XGBoost & SHAP TreeExplainer
├── fraud_model.joblib      # Trained XGBoost classification model
├── scaler.joblib           # Fitted StandardScaler pipeline
├── model_columns.joblib    # Ordered feature columns list
├── config.py               # Pydantic Settings and environment management
├── schema.sql              # Supabase table schema & RLS policies
├── requirements.txt        # Python package dependencies
├── .env                    # Environment variables (Supabase URL & Key)
├── models/
│   └── schemas.py          # Pydantic request/response validation schemas
└── tests/
    └── test_predict.py     # Pytest test suite
```

---

## Quickstart Guide

### 1. Create and Activate a Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```ini
# Supabase Credentials (Used by supabase-py client)
SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
SUPABASE_KEY=[YOUR-SUPABASE-ANON-OR-SERVICE-KEY]

# Local Next.js frontend URL
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> **Note**: If `DATABASE_URL` is not yet configured, the server operates smoothly in development mode, falling back to structured local audit logs so you can build and test immediately.

### 3. Initialize Supabase Database Table

Run the contents of [`schema.sql`](file:///Users/user/Desktop/GEN%20AI%20CIA/backend/schema.sql) in your **Supabase Dashboard -> SQL Editor**.

### 4. Run the Development Server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Reference

### `POST /predict`

Evaluates an incoming credit card transaction.

#### Sample Request Body:

```json
{
  "Time": 406.0,
  "Amount": 149.62,
  "V1": -2.3122, "V2": 1.9519, "V3": -1.6098, "V4": 3.9979,
  "V5": -0.5221, "V6": -1.4265, "V7": -2.5373, "V8": 1.3916,
  "V9": -2.7700, "V10": -2.7722, "V11": 3.2020, "V12": -2.8999,
  "V13": -0.5952, "V14": -4.2892, "V15": 0.3897, "V16": -1.1407,
  "V17": -2.8300, "V18": -0.0168, "V19": 0.4169, "V20": 0.1269,
  "V21": 0.5172, "V22": -0.0350, "V23": -0.4652, "V24": 0.3201,
  "V25": 0.0445, "V26": 0.1778, "V27": 0.2611, "V28": -0.1432
}
```

#### Sample Response:

```json
{
  "transaction_id": "txn_8b1d9c2e0f4a1789",
  "timestamp": "2026-11-04T04:05:00.000Z",
  "fraud_probability": 0.8842,
  "is_fraud": true,
  "risk_level": "CRITICAL",
  "shap_values": {
    "V14": 3.6459,
    "V4": 2.3987,
    "V12": 1.8849,
    "Amount": 0.1200,
    "Time": -0.0210
  },
  "top_contributors": [
    {
      "feature": "V14",
      "shap_value": 3.6459,
      "direction": "RISK_INCREASING",
      "description": "Latent merchant-category anomaly vector"
    }
  ],
  "model_version": "xgb-ensemble-v2.4-sim",
  "logged_to_database": true
}
```

---

## Running Automated Tests

```bash
pytest backend/tests/ -v
```

