from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(name="fixed_rate")
def fixed_rate_fixture(monkeypatch):
    """Pin the exchange rate so totals are predictable in tests."""

    def fake_rate():
        return Decimal("1500.00"), "live"

    monkeypatch.setattr("app.main.get_usd_to_ngn", fake_rate)
    return Decimal("1500.00")


SAMPLE = {
    "title": "MTN data bundle",
    "amount": "3500.00",
    "currency": "NGN",
    "category": "Data & airtime",
    "date": "2026-10-03",
}
