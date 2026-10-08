"""USD -> NGN exchange rate, from a free live API with an honest fallback."""

from decimal import Decimal

import httpx

RATE_API_URL = "https://open.er-api.com/v6/latest/USD"

# Used only when the live API is unreachable. Update occasionally.
# (Live rate was ~1330 on 2026-10-08 — the response labels this value as "fallback".)
FALLBACK_RATE = Decimal("1330.00")


def get_usd_to_ngn() -> tuple[Decimal, str]:
    """Return (rate, source). source is "live" or "fallback"."""
    try:
        resp = httpx.get(RATE_API_URL, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        rate = data["rates"]["NGN"]
        return Decimal(str(rate)), "live"
    except (httpx.HTTPError, KeyError, ValueError):
        return FALLBACK_RATE, "fallback"
