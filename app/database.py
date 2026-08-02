import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from app.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# For PostgreSQL in production, use NullPool to avoid connection pool issues in Docker
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
else:
    # For SQLite in tests, use default pool
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
