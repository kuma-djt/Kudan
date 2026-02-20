from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Strategy(ABC):
    name: str
    universe: list[str]
    timeframe: str = "1m"

    @abstractmethod
    def generate_targets(self, market_data: dict[str, list[float]]) -> dict[str, float]: ...


class MomentumStrategy(Strategy):
    name = "momentum"

    def __init__(self, universe: list[str]) -> None:
        self.universe = universe

    def generate_targets(self, market_data: dict[str, list[float]]) -> dict[str, float]:
        targets: dict[str, float] = {}
        for symbol in self.universe:
            series = market_data[symbol]
            targets[symbol] = 0.1 if series[-1] > series[0] else 0.0
        return targets


class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def __init__(self, universe: list[str]) -> None:
        self.universe = universe

    def generate_targets(self, market_data: dict[str, list[float]]) -> dict[str, float]:
        targets: dict[str, float] = {}
        for symbol in self.universe:
            series = market_data[symbol]
            mean = sum(series) / len(series)
            targets[symbol] = 0.08 if series[-1] < mean * 0.98 else 0.0
        return targets


def build_strategy(name: str, config: dict[str, Any]) -> Strategy:
    symbols = config.get("symbols", ["BTCUSD", "ETHUSD"])
    if name == "momentum":
        return MomentumStrategy(symbols)
    if name == "mean_reversion":
        return MeanReversionStrategy(symbols)
    raise ValueError(f"Unknown strategy {name}")
