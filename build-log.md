# Build log — every real error and mistake (nothing invented)

Session: 2026-10-08, Windows 11, Python 3.12.10. The AI (Claude) wrote the code; these are
the things that actually went wrong and how they were fixed.

## 1. The AI guessed the fallback exchange rate badly wrong

`app/rates.py` ships a hard-coded fallback for when the live rate API is down. The AI set
it from memory:

```python
FALLBACK_RATE = Decimal("1480.00")
```

Then the very first real call to `/summary` came back with the **live** rate:

```json
"usd_to_ngn_rate": "1330.207024", "rate_source": "live"
```

The guess was ~₦150 off (about 11%). If the rate API had gone down, every USD conversion
would have been silently inflated. Fix: updated the fallback to `1330.00` with a dated
comment, and the response always carries `rate_source: "live" | "fallback"` so users can
see which one they got. Lesson: never let an AI (or anyone) hard-code a "current" number
from memory — check it against a live source.

## 2. PowerShell's fake `curl` broke the demo commands

First attempt to demo the API in PowerShell failed — not an API bug, a Windows trap:

```
PS> curl -X POST http://127.0.0.1:8000/expenses -H "Content-Type: application/json" -d '{...}'
Invoke-WebRequest : Cannot bind parameter 'Headers'. Cannot convert the
"Content-Type: application/json" value of type "System.String" to type
"System.Collections.IDictionary".
```

Windows PowerShell aliases `curl` to `Invoke-WebRequest`, which has completely different
flags. Fix: call `curl.exe` explicitly (or run the commands in Git Bash). Verified working
— see recording.md §5.

## 3. Headless-Edge screenshot of /docs failed on the first try

Not an API issue, but real: `msedge --headless --screenshot=...` produced no file (old
headless mode + a running Edge instance grabbing the profile). Fix: `--headless=new` plus
a separate `--user-data-dir`. Second attempt produced `screenshots/docs-swagger.png`.

## What did NOT go wrong (for honesty in the video)

- All 21 pytest tests passed on the first run. The error cases above were caught before
  tests ran (the rate guess) or outside the app itself (PowerShell, screenshots).
- `pip install` and `uvicorn` startup were clean on the first attempt.
