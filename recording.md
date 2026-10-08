# NairaTrack API — real build & demo recording

Everything below is real output from the actual build session on **2026-10-08** (Windows 11,
Python 3.12.10). Nothing is mocked or retyped. These snippets are the source of truth for
the video script — do not "improve" them.

## 1. Setup

```
$ python -m venv .venv
$ .venv/Scripts/pip install -r requirements.txt
...
(installed fastapi 0.115.6, sqlmodel 0.0.22, uvicorn 0.34.0, httpx 0.28.1, pytest 8.3.4)
```

## 2. Test run (after the fallback-rate fix — see build-log.md)

```
$ .venv/Scripts/python -m pytest -q
21 passed, 1 warning in 0.21s
```

First full verbose run (all 21 tests, real):

```
tests/test_expenses.py::test_create_expense PASSED                       [  4%]
tests/test_expenses.py::test_create_expense_rejects_negative_amount PASSED [  9%]
tests/test_expenses.py::test_create_expense_rejects_zero_amount PASSED   [ 14%]
tests/test_expenses.py::test_create_expense_rejects_unknown_currency PASSED [ 19%]
tests/test_expenses.py::test_create_expense_rejects_unknown_category PASSED [ 23%]
tests/test_expenses.py::test_create_expense_rejects_blank_title PASSED   [ 28%]
tests/test_expenses.py::test_create_expense_rejects_bad_date PASSED      [ 33%]
tests/test_expenses.py::test_create_expense_rejects_too_many_decimal_places PASSED [ 38%]
tests/test_expenses.py::test_list_expenses_empty PASSED                  [ 42%]
tests/test_expenses.py::test_list_expenses_and_month_filter PASSED       [ 47%]
tests/test_expenses.py::test_list_expenses_rejects_bad_month PASSED      [ 52%]
tests/test_expenses.py::test_get_expense_by_id PASSED                    [ 57%]
tests/test_expenses.py::test_get_expense_404 PASSED                      [ 61%]
tests/test_expenses.py::test_delete_expense PASSED                       [ 66%]
tests/test_expenses.py::test_delete_expense_404 PASSED                   [ 71%]
tests/test_summary.py::test_summary_totals_mixed_currencies PASSED       [ 76%]
tests/test_summary.py::test_summary_empty_month PASSED                   [ 80%]
tests/test_summary.py::test_summary_requires_month PASSED                [ 85%]
tests/test_summary.py::test_summary_rejects_bad_month PASSED             [ 90%]
tests/test_summary.py::test_summary_uses_fallback_when_rate_api_down PASSED [ 95%]
tests/test_summary.py::test_rate_fallback_on_bad_json PASSED             [100%]
======================== 21 passed, 1 warning in 0.31s ========================
```

## 3. Run the server

```
$ .venv/Scripts/python -m uvicorn app.main:app --port 8000
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 4. Real curl session (Git Bash / curl.exe)

### POST /expenses — add an NGN expense

```
$ curl -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" \
  -d '{"title": "MTN data bundle", "amount": "3500.00", "currency": "NGN", "category": "Data & airtime", "date": "2026-10-03"}'
{"title":"MTN data bundle","amount":"3500.00","currency":"NGN","category":"Data & airtime","date":"2026-10-03","id":1}
```

### POST /expenses — two more (transport NGN, domain USD)

```
$ curl -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" \
  -d '{"title": "Bolt to Yaba", "amount": "4200.00", "currency": "NGN", "category": "Transport", "date": "2026-10-05"}'
{"title":"Bolt to Yaba","amount":"4200.00","currency":"NGN","category":"Transport","date":"2026-10-05","id":2}

$ curl -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" \
  -d '{"title": "Domain renewal", "amount": "12.00", "currency": "USD", "category": "Other", "date": "2026-10-06"}'
{"title":"Domain renewal","amount":"12.00","currency":"USD","category":"Other","date":"2026-10-06","id":3}
```

### POST /expenses — bad input is rejected with clear messages

```
$ curl -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" \
  -d '{"title": "Oops", "amount": "-50", "currency": "NGN", "category": "Food", "date": "2026-10-06"}'
{"detail":[{"type":"greater_than","loc":["body","amount"],"msg":"Input should be greater than 0","input":"-50","ctx":{"gt":0}}]}

$ curl -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" \
  -d '{"title": "Coffee", "amount": "5.00", "currency": "EUR", "category": "Food", "date": "2026-10-06"}'
{"detail":[{"type":"enum","loc":["body","currency"],"msg":"Input should be 'NGN' or 'USD'","input":"EUR","ctx":{"expected":"'NGN' or 'USD'"}}]}
```

### GET /expenses (all, and filtered by month)

```
$ curl -s "http://127.0.0.1:8000/expenses?month=2026-10"
[{"title":"Domain renewal","amount":"12.00","currency":"USD","category":"Other","date":"2026-10-06","id":3},{"title":"Bolt to Yaba","amount":"4200.00","currency":"NGN","category":"Transport","date":"2026-10-05","id":2},{"title":"MTN data bundle","amount":"3500.00","currency":"NGN","category":"Data & airtime","date":"2026-10-03","id":1}]
```

### GET /expenses/{id} — found and not found

```
$ curl -s http://127.0.0.1:8000/expenses/1
{"title":"MTN data bundle","amount":"3500.00","currency":"NGN","category":"Data & airtime","date":"2026-10-03","id":1}

$ curl -s http://127.0.0.1:8000/expenses/999
{"detail":"Expense not found"}
```

### GET /summary — real live exchange rate

```
$ curl -s "http://127.0.0.1:8000/summary?month=2026-10"
{"month":"2026-10","count":3,"total_ngn":"23662.48","total_usd":"17.79","usd_to_ngn_rate":"1330.207024","rate_source":"live","by_category_ngn":{"Data & airtime":"3500.00","Other":"15962.48","Transport":"4200.00"}}
```

The rate `1330.207024` came live from https://open.er-api.com/v6/latest/USD during the
session. With the rate API blocked (tested in pytest), `rate_source` flips to `"fallback"`
and the fallback rate is used.

### DELETE /expenses/{id}

```
$ curl -s -i -X DELETE http://127.0.0.1:8000/expenses/2
HTTP/1.1 204 No Content
date: Thu, 08 Oct 2026 06:07:43 GMT
server: uvicorn
```

## 5. Real Windows gotcha (PowerShell)

In Windows PowerShell, `curl` is an alias for `Invoke-WebRequest`, so the normal curl
command fails:

```
PS> curl -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" -d '{...}'
Invoke-WebRequest : Cannot bind parameter 'Headers'. Cannot convert the
"Content-Type: application/json" value of type "System.String" to type
"System.Collections.IDictionary".
```

Fix: call `curl.exe` explicitly (and escape the inner quotes):

```
PS> curl.exe -s -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" -d '{\"title\": \"Suya run\", \"amount\": \"2500.00\", \"currency\": \"NGN\", \"category\": \"Food\", \"date\": \"2026-10-07\"}'
{"title":"Suya run","amount":"2500.00","currency":"NGN","category":"Food","date":"2026-10-07","id":4}
```

## 6. Swagger UI

Screenshot of the auto-generated docs at http://127.0.0.1:8000/docs:
`screenshots/docs-swagger.png` — shows POST /expenses, GET /expenses,
GET /expenses/{expense_id}, DELETE /expenses/{expense_id}, GET /summary, plus the
Category/Currency/ExpenseCreate/ExpenseRead schemas. FastAPI generated all of it from
the code; we wrote zero lines of documentation.

## 7. Live deployment (Render free tier) — real output, 2026-10-08

Deployed via render.yaml Blueprint to https://nairatrack-api.onrender.com

```
$ curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" https://nairatrack-api.onrender.com/docs
200 3.443975s
```

Posted the same three expenses to the live API (ids 1–3 returned), then:

```
$ curl -s "https://nairatrack-api.onrender.com/summary?month=2026-10"
{"month":"2026-10","count":3,"total_ngn":"23662.48","total_usd":"17.79","usd_to_ngn_rate":"1330.207024","rate_source":"live","by_category_ngn":{"Data & airtime":"3500.00","Other":"15962.48","Transport":"4200.00"}}
```

Note: this run was warm. The free tier spins down when idle — the first request after a
quiet period takes ~30–60s while the service wakes (the video says so honestly).
SQLite data is wiped on redeploys.
