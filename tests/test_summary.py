import httpx

from app import rates
from tests.conftest import SAMPLE


def test_summary_totals_mixed_currencies(client, fixed_rate):
    client.post("/expenses", json=SAMPLE)  # NGN 3500
    client.post("/expenses", json=dict(SAMPLE, title="Domain renewal", currency="USD",
                                       amount="12.00", category="Other"))

    resp = client.get("/summary", params={"month": "2026-10"})
    assert resp.status_code == 200
    body = resp.json()
    # 3500 + 12 * 1500 = 21500 NGN
    assert body["count"] == 2
    assert body["total_ngn"] == "21500.00"
    assert body["total_usd"] == "14.33"  # 21500 / 1500, rounded to 2 places
    assert body["rate_source"] == "live"
    assert body["by_category_ngn"] == {
        "Data & airtime": "3500.00",
        "Other": "18000.00",
    }


def test_summary_empty_month(client, fixed_rate):
    resp = client.get("/summary", params={"month": "2026-01"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["total_ngn"] == "0.00"
    assert body["total_usd"] == "0.00"


def test_summary_requires_month(client):
    resp = client.get("/summary")
    assert resp.status_code == 422


def test_summary_rejects_bad_month(client):
    resp = client.get("/summary", params={"month": "10-2026"})
    assert resp.status_code == 422


def test_summary_uses_fallback_when_rate_api_down(client, monkeypatch):
    def boom(*args, **kwargs):
        raise httpx.ConnectError("rate API is down")

    monkeypatch.setattr(httpx, "get", boom)

    client.post("/expenses", json=SAMPLE)
    resp = client.get("/summary", params={"month": "2026-10"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["rate_source"] == "fallback"
    assert body["usd_to_ngn_rate"] == str(rates.FALLBACK_RATE)


def test_rate_fallback_on_bad_json(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": "shape"}

    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse())
    rate, source = rates.get_usd_to_ngn()
    assert source == "fallback"
    assert rate == rates.FALLBACK_RATE
