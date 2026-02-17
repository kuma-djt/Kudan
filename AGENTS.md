# AGENTS.md — KudanForge repo rules

## Non-negotiables
- Default to paper trading.
- Live trading requires BOTH:
  1) LIVE_TRADING=true (env)
  2) UI arming step with typed phrase: "ARM LIVE TRADING"
- Never commit secrets. Use env vars + .env.example.
- Never log API keys, secrets, auth headers, or wallet private keys.
- Risk Governor is authoritative: it can block orders, pause trading, and flatten positions.

## Dohndo-style risk defaults (configurable)
- Max drawdown from peak: 25% → pause trading + require manual resume
- Max daily loss: 2% → pause trading
- Per-trade risk budget: 0.25% equity
- Max gross exposure: 1.0 (no leverage)
- Rate limit orders: max 30/hour

## Engineering rules
- Python 3.11+
- FastAPI + server-rendered UI (HTMX preferred)
- SQLite persistence
- Tests required for risk checks and broker adapter mocks
- Provide make targets: dev/test/lint/up/down
- Provide /healthz endpoint and a smoke test
