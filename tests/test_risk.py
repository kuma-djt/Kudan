from app import db
from app.risk import RiskGovernor, ensure_live_gate


def test_risk_blocks_per_trade_limit() -> None:
    gov = RiskGovernor()
    decision = gov.evaluate(
        equity=100000,
        gross_exposure=0.5,
        order_notional=100000,
        orders_last_hour=1,
    )
    assert not decision.allowed
    assert "per_trade_risk_exceeded" in decision.reasons


def test_live_gate_needs_arming() -> None:
    db.set_state("armed_live", "false")
    decision = ensure_live_gate()
    assert not decision.allowed
    assert any("not armed" in reason.lower() for reason in decision.reasons)
