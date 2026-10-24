"""SQLAlchemy engine, session factory, and declarative base."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


if settings.sqlalchemy_database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Force IPv4 and require SSL for Supabase on Render's free tier.
    # Render free tier is IPv4-only; Supabase resolves to IPv6 by default.
    connect_args = {
        "sslmode": "require",
        "gssencmode": "disable",
    }

engine = create_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
