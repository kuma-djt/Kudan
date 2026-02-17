# KudanForge

KudanForge is a Dockerized VPS app that runs a paper-first crypto trading agent (Kudan) with strict risk controls.

## Safety defaults
- Paper trading by default.
- Live trading requires explicit arming via env var + UI confirmation phrase.

## Quick start (local)
1) Copy `.env.example` to `.env` and fill in paper keys.
2) `make up`
3) Visit `http://localhost:8080`

## VPS
See `docs/DEPLOYMENT_VPS.md`.

## Warning
This project is experimental. No guarantees. Use paper trading until you’ve validated a thesis and tuned risk constraints.
