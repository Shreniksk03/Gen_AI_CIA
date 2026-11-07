from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TransactionPayload(BaseModel):
    """
    Financial Fraud Detection transaction payload matching the trained 35-feature schema:
    Supports both standard field names (transaction_amount) and aliases (amount, Amount).
    All fields provide robust domain defaults to ensure resilient ingestion.
    """
    # Key Financial Metrics
    transaction_amount: float = Field(default=100.0, ge=0.0, description="Transaction monetary amount")
    amount: Optional[float] = Field(default=None, description="Alias for transaction_amount")
    Amount: Optional[float] = Field(default=None, description="Legacy alias for transaction_amount")
    
    # Temporal & Behavioral
    transaction_hour: int = Field(default=12, ge=0, le=23, description="Hour of day (0-23)")
    transaction_day_of_week: str = Field(default="Monday", description="Day of week")
    is_weekend: int = Field(default=0, ge=0, le=1, description="1 if weekend, else 0")
    days_since_last_transaction: float = Field(default=1.0, ge=0.0)
    
    # Cardholder & Account Profile
    customer_age: int = Field(default=35, ge=18, le=120)
    customer_gender: str = Field(default="Female")
    customer_state: str = Field(default="CA")
    account_age_days: int = Field(default=365, ge=0)
    credit_score: int = Field(default=700, ge=300, le=850)
    credit_limit: float = Field(default=5000.0, ge=0.0)
    num_cards_held: int = Field(default=2, ge=1)
    
    # Velocity & Spending Pattern Baselines
    transactions_last_1h: int = Field(default=1, ge=0)
    transactions_last_24h: int = Field(default=2, ge=0)
    transactions_last_7d: int = Field(default=8, ge=0)
    amount_last_1h: float = Field(default=100.0, ge=0.0)
    amount_last_24h: float = Field(default=250.0, ge=0.0)
    avg_transaction_amount_30d: float = Field(default=95.0, ge=0.0)
    std_transaction_amount_30d: float = Field(default=45.0, ge=0.0)
    amount_vs_avg_ratio: float = Field(default=1.05, ge=0.0)
    
    # Geolocation & Channel
    distance_from_home_km: float = Field(default=15.0, ge=0.0)
    distance_from_last_tx_km: float = Field(default=5.0, ge=0.0)
    international_transaction: int = Field(default=0, ge=0, le=1)
    high_risk_country: int = Field(default=0, ge=0, le=1)
    merchant_category: str = Field(default="Online Retail")
    merchant_country: str = Field(default="USA")
    transaction_channel: str = Field(default="Online")
    
    # Security, Device & Authentication
    card_present: int = Field(default=0, ge=0, le=1)
    used_chip: int = Field(default=0, ge=0, le=1)
    used_pin: int = Field(default=0, ge=0, le=1)
    device_type: str = Field(default="Mobile")
    browser: str = Field(default="Chrome")
    email_domain: str = Field(default="gmail")
    
    # Negative Risk Indicators
    num_declined_last_30d: int = Field(default=0, ge=0)
    num_chargebacks_ever: int = Field(default=0, ge=0)

    # Optional metadata identifiers
    transaction_id: Optional[str] = None
    merchant: Optional[str] = None
    location: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )

    @model_validator(mode="after")
    def reconcile_amount_aliases(self) -> "TransactionPayload":
        if self.Amount is not None:
            self.transaction_amount = float(self.Amount)
        elif self.amount is not None:
            self.transaction_amount = float(self.amount)
        return self


class FeatureImpact(BaseModel):
    feature: str
    display_name: str = ""
    shap_value: float
    feature_value: Any = None
    direction: Literal["RISK_INCREASING", "RISK_DECREASING"] = "RISK_INCREASING"
    impact: Literal["INCREASED_RISK", "REDUCED_RISK"] = "INCREASED_RISK"
    description: str = ""
    human_readable: str = ""


class PredictionResponse(BaseModel):
    transaction_id: str = Field(..., description="Unique UUID for this transaction event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fraud_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model-estimated probability of fraud (0.0 to 1.0)",
        examples=[0.874]
    )
    is_fraud: bool = Field(..., description="True if probability exceeds decision threshold (0.35)")
    is_flagged: bool = Field(..., description="True if fraud probability meets operational threshold")
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        ...,
        description="Categorical risk stratification: LOW (<0.25), MEDIUM (0.25-0.60), HIGH (>=0.60)"
    )
    review_status: str = Field(default="PENDING")
    base_value: float = Field(
        default=0.0,
        description="SHAP expected baseline value E[f(x)]"
    )
    shap_values: Dict[str, float] = Field(
        ...,
        description="Feature attribution values explaining prediction impact"
    )
    shap_explanations: Dict[str, float] = Field(
        default_factory=dict,
        description="SHAP explanations dictionary"
    )
    top_contributors: List[FeatureImpact] = Field(
        ...,
        description="Top 5 contributing features ranked by absolute SHAP impact"
    )
    positive_contributions: List[FeatureImpact] = Field(
        default_factory=list,
        description="Features that increased fraud risk (SHAP > 0)"
    )
    negative_contributions: List[FeatureImpact] = Field(
        default_factory=list,
        description="Features that reduced fraud risk (SHAP < 0)"
    )
    summary_narrative: List[str] = Field(
        default_factory=list,
        description="Plain-language human-readable explainability narrative"
    )
    model_version: str = Field(default="xgboost-tree-explainer-v2.0")
    logged_to_database: bool = Field(
        default=False,
        description="Whether this transaction was successfully persisted into the database"
    )
    database_source: Optional[str] = Field(
        default=None,
        description="Active authoritative database source (SUPABASE_POSTGRESQL or SQLITE_FALLBACK)"
    )
    database_source_label: Optional[str] = Field(
        default=None,
        description="Human-readable data source label"
    )
    supabase_persisted: bool = Field(default=False)
    sqlite_persisted: bool = Field(default=False)


ReviewStatusType = Literal["PENDING", "UNDER_REVIEW", "CONFIRMED_FRAUD", "LEGITIMATE", "ESCALATED"]


class ReviewHistoryItem(BaseModel):
    id: str
    transaction_id: str
    previous_status: Optional[str] = None
    new_status: str
    analyst_notes: Optional[str] = None
    reviewed_by: str
    created_at: str


class ReviewUpdateRequest(BaseModel):
    review_status: ReviewStatusType
    analyst_notes: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: str = Field(default="analyst@sentinel.internal", max_length=100)


class TransactionRecord(BaseModel):
    """Normalized schema for transactions persisted in database and returned to dashboard."""
    id: str
    transaction_time: str
    amount: float
    fraud_probability: float
    is_flagged: bool
    risk_level: str = "LOW"
    review_status: str = "PENDING"
    merchant: Optional[str] = "Unknown Merchant"
    merchant_category: Optional[str] = "Online Retail"
    location: Optional[str] = "Unknown Location"
    category: Optional[str] = "Retail"
    card_last4: Optional[str] = "4242"
    model_version: Optional[str] = "xgboost-tree-explainer-v2.0"
    analyst_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    shap_explanations: Optional[Dict[str, float]] = None
    top_contributors: Optional[List[Dict[str, Any]]] = None
    summary_narrative: Optional[List[str]] = None
    v_features: Optional[Dict[str, Any]] = None
    review_history: Optional[List[ReviewHistoryItem]] = None


class PaginatedTransactionsResponse(BaseModel):
    items: List[TransactionRecord]
    total: int
    page: int
    limit: int
    pages: int
    data_source: Optional[str] = "SQLITE_FALLBACK"
    data_source_label: Optional[str] = "Data Source: Local SQLite (Fallback)"


class VolumeTimeSeriesPoint(BaseModel):
    timestamp: str
    count: int
    volume_amount: float


class FraudTimeSeriesPoint(BaseModel):
    timestamp: str
    flagged_count: int
    flagged_amount: float


class AnalyticsResponse(BaseModel):
    time_range: str
    total_transactions: int
    total_flagged_transactions: int
    total_not_flagged_transactions: Optional[int] = 0
    total_confirmed_fraud: int
    total_confirmed_legitimate: Optional[int] = 0
    total_legitimate: int
    transactions_awaiting_review: int
    transactions_under_review: Optional[int] = 0
    transactions_escalated: Optional[int] = 0
    fraud_detection_rate: float
    fraud_percentage: float
    risk_distribution: Dict[str, int]
    review_status_distribution: Optional[Dict[str, int]] = None
    volume_over_time: List[VolumeTimeSeriesPoint]
    fraud_volume_over_time: List[FraudTimeSeriesPoint]
    data_source: Optional[str] = "SQLITE_FALLBACK"
    data_source_label: Optional[str] = "Data Source: Local SQLite (Fallback)"


class ModelInfoResponse(BaseModel):
    model_name: str
    algorithm: str
    version: str
    training_date: str
    number_of_features: int
    number_of_encoded_features: int
    input_feature_schema: List[str]
    preprocessing: Dict[str, Any]
    shap_output_space: str
    selected_threshold: float
    decision_rationale: str
    risk_band_configuration: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database_connected: bool
    database_source: Optional[str] = "SQLITE_FALLBACK"
    database_source_label: Optional[str] = "Data Source: Local SQLite (Fallback)"
    supabase_status: Optional[str] = "DISCONNECTED"
    sqlite_status: Optional[str] = "ACTIVE"
    sqlite_records_count: Optional[int] = 0
    supabase_records_count: Optional[int] = 0
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
