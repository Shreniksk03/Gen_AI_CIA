import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.config import settings

logger = logging.getLogger("fraud_backend.db")

# Global async session factory for PostgreSQL
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_engine = None
_supabase_client = None


def get_supabase_client():
    """Initializes or returns cached Supabase REST Client if credentials exist."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client, Client
            _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Connected to Supabase via REST Client.")
            return _supabase_client
        except Exception as e:
            logger.warning(f"Could not initialize Supabase REST client: {e}")
            return None
    return None


async def init_db():
    """Initializes async PostgreSQL connection pool if DATABASE_URL is configured."""
    global _engine, _async_session_factory
    if settings.DATABASE_URL:
        try:
            db_url = settings.DATABASE_URL
            # Normalize driver for asyncpg
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

            _engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_recycle=1800,
                pool_pre_ping=True
            )
            _async_session_factory = async_sessionmaker(
                bind=_engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            logger.info("Initialized PostgreSQL async engine connection pool.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL pool: {e}")


async def close_db():
    """Closes database connection pools on shutdown."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Closed PostgreSQL connection pool.")


def get_session_factory() -> Optional[async_sessionmaker[AsyncSession]]:
    return _async_session_factory

