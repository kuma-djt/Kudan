from __future__ import annotations

from dataclasses import dataclass

from app import db
from app.config import settings


@dataclass(slots=True)
class RiskDecision:
    allowed: bool
    reasons: list[str]
    pause: bool = False
    kill_switch: bool = False


class RiskGovernor:
    def __init__(self) -> None:
        self.max_drawdown = settings.max_drawdown_from_peak
        self.max_daily_loss = settings.max_daily_loss
        self.per_trade_risk = settings.per_trade_risk
        self.max_gross_exposure = settings.max_gross_exposure
        self.max_orders_per_hour = settings.max_orders_per_hour

    def evaluate(
        self,
        equity: float,
        gross_exposure: float,
        order_notional: float,
        orders_last_hour: int,
    ) -> RiskDecision:
        reasons: list[str] = []
        pause = False
        kill = db.get_state("kill_switch", "false") == "true"

        peak = float(db.get_state("peak_equity", "100000"))
        day_start = float(db.get_state("day_start_equity", str(equity)))
        drawdown = 0.0 if peak <= 0 else max(0.0, (peak - equity) / peak)
        daily_loss = 0.0 if day_start <= 0 else max(0.0, (day_start - equity) / day_start)

        if equity > peak:
            db.set_state("peak_equity", str(equity))

        if drawdown >= self.max_drawdown:
            reasons.append("max_drawdown_exceeded")
            pause = True

        if daily_loss >= self.max_daily_loss:
            reasons.append("max_daily_loss_exceeded")
            pause = True

        if gross_exposure > self.max_gross_exposure:
            reasons.append("max_gross_exposure_exceeded")

        if order_notional > equity * self.per_trade_risk:
            reasons.append("per_trade_risk_exceeded")

        if orders_last_hour >= self.max_orders_per_hour:
            reasons.append("max_orders_per_hour_exceeded")

        if kill:
            reasons.append("kill_switch_enabled")

        if pause:
            db.set_state("paused", "true")

        allowed = len(reasons) == 0
        if not allowed:
            for reason in reasons:
                db.insert_risk_event(
                    level="block",
                    reason=reason,
                    context={
                        "equity": equity,
                        "gross_exposure": gross_exposure,
                        "order_notional": order_notional,
                        "orders_last_hour": orders_last_hour,
                    },
                )
        return RiskDecision(allowed=allowed, reasons=reasons, pause=pause, kill_switch=kill)


def is_live_allowed() -> bool:
    return settings.live_trading_env and db.get_state("armed_live", "false") == "true"


def ensure_live_gate() -> RiskDecision:
    if is_live_allowed():
        return RiskDecision(allowed=True, reasons=[])
    reasons = []
    if not settings.live_trading_env:
        reasons.append("LIVE_TRADING env var disabled")
    if db.get_state("armed_live", "false") != "true":
        reasons.append("System is not armed in UI")
    return RiskDecision(allowed=False, reasons=reasons)
