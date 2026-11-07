import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from supabase import Client
from backend.models.schemas import TransactionPayload

logger = logging.getLogger("fraud_backend.db_service")


async def log_transaction_to_supabase(
    transaction_id: str,
    payload: TransactionPayload,
    fraud_probability: float,
    risk_level: str,
    is_fraud: bool,
    shap_values: Dict[str, float],
    timestamp: Optional[datetime] = None,
    client_ip: Optional[str] = None,
    client: Optional[Client] = None,
) -> bool:
    """
    Persists incoming credit card transaction, its generated probability score,
    and the timestamp into the Supabase 'transactions' table using supabase-py.
    """
    from backend.main import get_supabase

    sb_client = client or get_supabase()
    ts = timestamp or datetime.now(timezone.utc)
    is_flagged = bool(fraud_probability > 0.8)

    if not sb_client:
        logger.warning(
            f"[OFFLINE AUDIT] Supabase unconfigured. Transaction {transaction_id} "
            f"| Amount: ${payload.Amount:.2f} | Prob: {fraud_probability:.4f} | is_flagged: {is_flagged}"
        )
        return False

    try:
        record_data = {
            "id": transaction_id,
            "transaction_time": ts.isoformat(),
            "amount": float(payload.Amount),
            "v_features": payload.get_pca_dict(),
            "fraud_probability": float(fraud_probability),
            "is_flagged": is_flagged,
            "shap_explanations": shap_values,
        }

        response = sb_client.table("transactions").insert(record_data).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Supabase REST insert error via supabase-py: {e}")
        return False
