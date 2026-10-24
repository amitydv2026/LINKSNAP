"""Pytest fixtures.

Tests run against SQLite by default for zero-setup local runs. In CI the
DATABASE_URL environment variable is set to Postgres, which overrides the
default (setdefault only sets when the var is missing), so CI exercises the
real Postgres path.
"""
import os

# Default to a local SQLite file for tests unless DATABASE_URL is already set
# (e.g. to Postgres in CI). Must run BEFORE importing the app so settings pick
# it up.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Click, Link, User  # noqa: E402,F401  (register tables on Base.metadata)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _isolate():
    """Reset the redirect cache before each test and wipe all rows after it."""
    from app.routes.redirect import redirect_cache

    redirect_cache.clear()
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    redirect_cache.clear()


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def user_token(client: TestClient) -> str:
    client.post("/auth/register", json={"email": "user@test.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "user@test.com", "password": "secret123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}
