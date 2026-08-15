import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/control_service.db")

# Ensure data directory exists if using local SQLite database
if DATABASE_URL.startswith("sqlite:///./data"):
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None):
    """Create all tables in the database."""
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)


def get_db():
    """FastAPI dependency for yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
