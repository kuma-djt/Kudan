# Risk Policy — Dohndo-style constraints for KudanForge

## Operating modes
1) Research only: no trading
2) Paper trading (default)
3) Canary live: tiny capital allocation, strict limits, short duration
4) Live: small portfolio only after validated thesis

## Mode promotion gates
Paper → Canary requires:
- Strategy has a written hypothesis + defined failure modes
- Backtest report with conservative fees/slippage
- No single-parameter fragility (basic sensitivity checks)
- Manual approval in UI

Canary → Live requires:
- Canary run meets predefined criteria (e.g., stable drawdown, no runaway turnover)
- Manual approval in UI + arming phrase

## Circuit breakers (defaults)
- Max drawdown from peak: 25% → pause trading
- Max daily loss: 2% → pause trading
- Max gross exposure: 1.0
- Per-trade risk: 0.25% equity
- Max orders/hour: 30

## “Reward creativity” without blowing up
- Innovation budget: cap experimental strategies to a small slice of equity (e.g., 5–10%)
- Graduated sizing: strategies earn allocation only after evidence
- Strategy must be reproducible (versioned config + stored report)
