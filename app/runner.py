from __future__ import annotations

import json
import threading
import time
from typing import Any

from app import db
from app.broker import BrokerAdapter, build_broker
from app.config import settings
from app.risk import RiskGovernor, ensure_live_gate
from app.strategies import build_strategy


class StrategyRunner:
    def __init__(self, broker: BrokerAdapter | None = None) -> None:
        self.broker = broker or build_broker()
        self.risk = RiskGovernor()

    def run_once(self) -> dict[str, Any]:
        account = self.broker.get_account()
        positions = self.broker.get_positions()
        pos_map = {p["symbol"]: float(p["qty"]) for p in positions}
        exposure = sum(abs(float(p["market_value"])) for p in positions)
        gross_exposure = 0.0 if account.equity <= 0 else exposure / account.equity

        decisions: list[dict[str, Any]] = []
        for strategy_row in db.list_strategies():
            if not strategy_row["enabled"]:
                continue
            strategy = build_strategy(strategy_row["name"], json.loads(strategy_row["config"]))
            market_data = {}
            for symbol in strategy.universe:
                latest = self.broker.get_latest_price(symbol)
                market_data[symbol] = [latest * 0.99, latest]
            targets = strategy.generate_targets(market_data)
            mode = strategy_row["mode"]
            for symbol, target_weight in targets.items():
                price = self.broker.get_latest_price(symbol)
                target_qty = (account.equity * target_weight) / price
                current_qty = pos_map.get(symbol, 0.0)
                delta = target_qty - current_qty
                if abs(delta) < 1e-6:
                    continue
                side = "buy" if delta > 0 else "sell"
                qty = abs(delta)
                order_notional = qty * price

                if mode == "live":
                    gate = ensure_live_gate()
                    if not gate.allowed:
                        decisions.append(
                            {"symbol": symbol, "status": "blocked", "reasons": gate.reasons}
                        )
                        continue

                decision = self.risk.evaluate(
                    equity=account.equity,
                    gross_exposure=gross_exposure,
                    order_notional=order_notional,
                    orders_last_hour=db.orders_in_last_hour(),
                )
                if not decision.allowed:
                    decisions.append(
                        {"symbol": symbol, "status": "risk_block", "reasons": decision.reasons}
                    )
                    continue

                order = self.broker.place_order(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    order_type="market",
                )
                decisions.append({"symbol": symbol, "status": "submitted", "order_id": order["id"]})

        status = (
            "ok"
            if all(d["status"] == "submitted" for d in decisions) or not decisions
            else "partial"
        )
        run_id = db.insert_run(
            status=status,
            summary=f"Cycle executed with {len(decisions)} decisions",
            details={"decisions": decisions},
        )
        for d in decisions:
            if d["status"] == "submitted":
                db.insert_order(run_id, d["symbol"], "buy", 1.0, "submitted", d.get("order_id"))
            else:
                db.insert_order(
                    run_id,
                    d["symbol"],
                    "buy",
                    0.0,
                    d["status"],
                    None,
                    ",".join(d.get("reasons", [])),
                )
        return {"run_id": run_id, "status": status, "decisions": decisions}


class Scheduler:
    def __init__(self, runner: StrategyRunner) -> None:
        self.runner = runner
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if not settings.scheduler_enabled or self._thread:
            return

        def loop() -> None:
            while not self._stop.is_set():
                self.runner.run_once()
                time.sleep(settings.scheduler_interval_seconds)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
