# NairaTrack API

A small expense-tracking REST API built with **FastAPI + SQLModel + SQLite**, made on the
[OS Techs](https://www.youtube.com/@ostechs) YouTube channel as a build-with-AI tutorial.

Track expenses in **NGN** and **USD**, with a monthly summary that converts using a live
USD→NGN rate (from [open.er-api.com](https://open.er-api.com), free, no key) and a clearly
labelled fallback rate when that API is unreachable.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| POST | `/expenses` | Add an expense |
| GET | `/expenses?month=YYYY-MM` | List expenses, optional month filter |
| GET | `/expenses/{id}` | Get one expense |
| DELETE | `/expenses/{id}` | Delete an expense |
| GET | `/summary?month=YYYY-MM` | Monthly totals in NGN and USD, by category |
| GET | `/docs` | Auto-generated Swagger UI |

## Run locally

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (use source .venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs

## Run the tests

```bash
pytest -v
```

## Deploy (Render free tier)

The repo includes a `render.yaml`. On [render.com](https://render.com): New → Blueprint →
connect this repo. Note: the free tier spins down when idle, so the first request after a
quiet period takes ~30–60 seconds. SQLite data is also wiped on redeploys — fine for a demo,
use a managed database for anything real.

## Example

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "MTN data bundle", "amount": "3500.00", "currency": "NGN", "category": "Data & airtime", "date": "2026-10-03"}'
```
