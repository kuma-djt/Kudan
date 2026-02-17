# Security

## Secrets
- Never commit secrets to the repo.
- Use environment variables for all credentials.
- Provide a .env.example with placeholder values.

## Logging
- Do not log request headers containing authorization.
- Do not log broker responses that include credentials.
- Redact known sensitive fields.

## Least privilege
- Prefer paper trading keys for development.
- Live trading must be explicitly armed and gated.

## VPS hardening (minimum)
- Run behind a reverse proxy if exposed publicly.
- Restrict inbound ports.
- Rotate keys if leakage is suspected.
