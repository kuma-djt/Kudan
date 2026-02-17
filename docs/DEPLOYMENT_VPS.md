# VPS Deployment

## Requirements
- Docker + docker compose on the VPS

## Steps
1) Copy `.env.example` to `.env` and set values.
2) `docker compose up -d --build`
3) Confirm `/healthz` returns ok
4) Optionally add a reverse proxy (nginx/caddy) + TLS

## Recommended
- Restrict inbound ports
- Put the UI behind auth if exposed
- Keep LIVE_TRADING disabled unless intentionally armed
