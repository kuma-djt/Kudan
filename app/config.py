from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_name: str = "KudanForge"
    db_path: str = os.getenv("KUDAN_DB_PATH", "/data/kudan.sqlite")
    live_trading_env: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
    scheduler_enabled: bool = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
    scheduler_interval_seconds: int = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    alpaca_api_key: str | None = os.getenv("ALPACA_API_KEY")
    alpaca_secret_key: str | None = os.getenv("ALPACA_SECRET_KEY")
    alpaca_base_url: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")

    max_drawdown_from_peak: float = float(os.getenv("RISK_MAX_DRAWDOWN", "0.25"))
    max_daily_loss: float = float(os.getenv("RISK_MAX_DAILY_LOSS", "0.02"))
    per_trade_risk: float = float(os.getenv("RISK_PER_TRADE", "0.0025"))
    max_gross_exposure: float = float(os.getenv("RISK_MAX_GROSS_EXPOSURE", "1.0"))
    max_orders_per_hour: int = int(os.getenv("RISK_MAX_ORDERS_PER_HOUR", "30"))

    @property
    def db_dir(self) -> Path:
        return Path(self.db_path).parent


settings = Settings()
