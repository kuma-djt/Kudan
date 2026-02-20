from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass(slots=True)
class Account:
    equity: float
    cash: float


class BrokerAdapter(ABC):
    @abstractmethod
    def get_account(self) -> Account: ...

    @abstractmethod
    def get_positions(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float: ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        order_type: str,
        limit_price: float | None = None,
    ) -> dict[str, Any]: ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict[str, Any]: ...


class BrokerMock(BrokerAdapter):
    def __init__(self) -> None:
        self.positions: dict[str, float] = {}
        self.prices = {"BTCUSD": 50000.0, "ETHUSD": 3000.0}
        self.equity = 100000.0

    def get_account(self) -> Account:
        return Account(equity=self.equity, cash=self.equity * 0.5)

    def get_positions(self) -> list[dict[str, Any]]:
        return [
            {"symbol": symbol, "qty": qty, "market_value": qty * self.get_latest_price(symbol)}
            for symbol, qty in self.positions.items()
            if qty != 0
        ]

    def get_latest_price(self, symbol: str) -> float:
        return self.prices.get(symbol, 100.0)

    def place_order(
        self, symbol: str, side: str, qty: float, order_type: str, limit_price: float | None = None
    ) -> dict[str, Any]:
        current = self.positions.get(symbol, 0.0)
        self.positions[symbol] = current + qty if side == "buy" else current - qty
        return {
            "id": f"mock-{symbol}-{qty}",
            "status": "accepted",
            "type": order_type,
            "limit_price": limit_price,
        }

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return {"id": order_id, "status": "canceled"}


class AlpacaCryptoBroker(BrokerAdapter):
    def __init__(self) -> None:
        if not settings.alpaca_api_key or not settings.alpaca_secret_key:
            raise ValueError("Alpaca credentials are missing")
        self.base_url = settings.alpaca_base_url.rstrip("/")
        self.headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
        }

    def _get(self, path: str) -> Any:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{self.base_url}{path}", headers=self.headers)
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{self.base_url}{path}", headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def _delete(self, path: str) -> Any:
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(f"{self.base_url}{path}", headers=self.headers)
            response.raise_for_status()
            return response.json()

    def get_account(self) -> Account:
        data = self._get("/v2/account")
        return Account(equity=float(data["equity"]), cash=float(data["cash"]))

    def get_positions(self) -> list[dict[str, Any]]:
        return self._get("/v2/positions")

    def get_latest_price(self, symbol: str) -> float:
        data = self._get(f"/v1beta3/crypto/us/latest/quotes?symbols={symbol}")
        return float(data["quotes"][symbol]["bp"])

    def place_order(
        self, symbol: str, side: str, qty: float, order_type: str, limit_price: float | None = None
    ) -> dict[str, Any]:
        payload = {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "type": order_type,
            "time_in_force": "gtc",
        }
        if limit_price is not None:
            payload["limit_price"] = limit_price
        return self._post("/v2/orders", payload)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return self._delete(f"/v2/orders/{order_id}")


def build_broker() -> BrokerAdapter:
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        return AlpacaCryptoBroker()
    return BrokerMock()
