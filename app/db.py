from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def init_db() -> None:
    Path(settings.db_dir).mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS config_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                mode TEXT NOT NULL DEFAULT 'paper',
                version TEXT NOT NULL DEFAULT 'v1'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                details TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                reason TEXT NOT NULL,
                context TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty REAL NOT NULL,
                status TEXT NOT NULL,
                broker_order_id TEXT,
                reason TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS position_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                qty REAL NOT NULL,
                market_value REAL NOT NULL
            )
            """
        )
        conn.commit()
        ensure_default_state(conn)
        ensure_default_strategies(conn)


def ensure_default_state(conn: sqlite3.Connection) -> None:
    for key, value in {
        "armed_live": "false",
        "kill_switch": "false",
        "paused": "false",
        "peak_equity": "100000",
        "day_start_equity": "100000",
    }.items():
        conn.execute(
            "INSERT OR IGNORE INTO config_state(key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, utcnow_iso()),
        )


def ensure_default_strategies(conn: sqlite3.Connection) -> None:
    existing = conn.execute("SELECT COUNT(*) FROM strategies").fetchone()[0]
    if existing:
        return
    defaults = [
        ("momentum", json.dumps({"symbols": ["BTCUSD", "ETHUSD"]}), 1, "paper", "v1"),
        ("mean_reversion", json.dumps({"symbols": ["BTCUSD", "ETHUSD"]}), 1, "paper", "v1"),
    ]
    conn.executemany(
        "INSERT INTO strategies(name, config, enabled, mode, version) VALUES (?, ?, ?, ?, ?)",
        defaults,
    )


@contextmanager
def get_conn() -> Any:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_state(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM config_state WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default


def set_state(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO config_state(key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, value, utcnow_iso()),
        )


def list_strategies() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM strategies ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def update_strategy_mode(strategy_id: int, mode: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE strategies SET mode = ? WHERE id = ?", (mode, strategy_id))


def insert_run(status: str, summary: str, details: dict[str, Any]) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO runs(created_at, status, summary, details) VALUES (?, ?, ?, ?)",
            (utcnow_iso(), status, summary, json.dumps(details)),
        )
        return int(cur.lastrowid)


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            item["details"] = json.loads(item["details"])
            out.append(item)
        return out


def insert_risk_event(level: str, reason: str, context: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO risk_events(created_at, level, reason, context) VALUES (?, ?, ?, ?)",
            (utcnow_iso(), level, reason, json.dumps(context)),
        )


def list_risk_events(limit: int = 50) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM risk_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            item["context"] = json.loads(item["context"])
            out.append(item)
        return out


def insert_order(
    run_id: int,
    symbol: str,
    side: str,
    qty: float,
    status: str,
    broker_order_id: str | None,
    reason: str | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO orders(
                run_id, created_at, symbol, side, qty, status, broker_order_id, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, utcnow_iso(), symbol, side, qty, status, broker_order_id, reason),
        )


def orders_in_last_hour() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE datetime(created_at) >= datetime('now', '-1 hour')"
        ).fetchone()
        return int(row[0])


def list_orders(limit: int = 100) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
