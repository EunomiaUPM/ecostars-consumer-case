# app/db.py
import logging
import os

from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env only in local development.
# In production (Docker), environment variables are injected directly.
# ---------------------------------------------------------------------------

if os.getenv("ENV") != "production":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env load")

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")

missing = [
    name for name, value in {
        "DATABASE_USER": DATABASE_USER,
        "DATABASE_PASSWORD": DATABASE_PASSWORD,
        "DATABASE_HOST": DATABASE_HOST,
        "DATABASE_PORT": DATABASE_PORT,
        "DATABASE_NAME": DATABASE_NAME,
    }.items()
    if not value
]

if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_engine(DATABASE_URL, echo=True)


# ---------------------------------------------------------------------------
# Table management
# ---------------------------------------------------------------------------

def create_db_and_tables(drop_first: bool = False) -> None:
    """
    Create all tables registered in SQLModel metadata.
    Set drop_first=True to wipe and recreate — use only during development.
    """
    if drop_first:
        logger.warning("Dropping all tables before recreating them")
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that yields a database session per request."""
    with Session(engine) as session:
        yield session