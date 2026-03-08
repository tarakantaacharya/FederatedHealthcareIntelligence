"""
MySQL database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes
    Yields database session and ensures cleanup
    """
    print("[DEPENDENCY] get_db() CALLED")
    import sys
    sys.stdout.flush()
    db = SessionLocal()
    try:
        print("[DEPENDENCY] get_db() YIELDING SESSION")
        sys.stdout.flush()
        yield db
    finally:
        print("[DEPENDENCY] get_db() CLOSING SESSION")
        sys.stdout.flush()
        db.close()
