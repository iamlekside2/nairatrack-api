from tests.conftest import SAMPLE


def test_create_expense(client):
    resp = client.post("/expenses", json=SAMPLE)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["title"] == "MTN data bundle"
    assert body["amount"] == "3500.00"
    assert body["currency"] == "NGN"
    assert body["category"] == "Data & airtime"


def test_create_expense_rejects_negative_amount(client):
    bad = dict(SAMPLE, amount="-500")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_zero_amount(client):
    bad = dict(SAMPLE, amount="0")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_unknown_currency(client):
    bad = dict(SAMPLE, currency="EUR")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_unknown_category(client):
    bad = dict(SAMPLE, category="Gambling")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_blank_title(client):
    bad = dict(SAMPLE, title="   ")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_bad_date(client):
    bad = dict(SAMPLE, date="03/10/2026")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_create_expense_rejects_too_many_decimal_places(client):
    bad = dict(SAMPLE, amount="100.999")
    resp = client.post("/expenses", json=bad)
    assert resp.status_code == 422


def test_list_expenses_empty(client):
    resp = client.get("/expenses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_expenses_and_month_filter(client):
    client.post("/expenses", json=SAMPLE)
    client.post("/expenses", json=dict(SAMPLE, title="Bolt ride", date="2026-09-20",
                                       category="Transport", amount="4200.00"))

    all_resp = client.get("/expenses")
    assert len(all_resp.json()) == 2

    oct_resp = client.get("/expenses", params={"month": "2026-10"})
    assert len(oct_resp.json()) == 1
    assert oct_resp.json()[0]["title"] == "MTN data bundle"

    sep_resp = client.get("/expenses", params={"month": "2026-09"})
    assert len(sep_resp.json()) == 1
    assert sep_resp.json()[0]["title"] == "Bolt ride"


def test_list_expenses_rejects_bad_month(client):
    resp = client.get("/expenses", params={"month": "October"})
    assert resp.status_code == 422

    resp = client.get("/expenses", params={"month": "2026-13"})
    assert resp.status_code == 422


def test_get_expense_by_id(client):
    created = client.post("/expenses", json=SAMPLE).json()
    resp = client.get(f"/expenses/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "MTN data bundle"


def test_get_expense_404(client):
    resp = client.get("/expenses/999")
    assert resp.status_code == 404


def test_delete_expense(client):
    created = client.post("/expenses", json=SAMPLE).json()
    resp = client.delete(f"/expenses/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/expenses/{created['id']}").status_code == 404


def test_delete_expense_404(client):
    resp = client.delete("/expenses/999")
    assert resp.status_code == 404
