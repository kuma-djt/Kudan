from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import db
from app.config import settings
from app.llm import LLMProvider
from app.risk import ensure_live_gate
from app.runner import Scheduler, StrategyRunner

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
runner = StrategyRunner()
scheduler = Scheduler(runner)
llm_provider = LLMProvider()


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    scheduler.start()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/state")
def api_state() -> dict:
    account = runner.broker.get_account()
    positions = runner.broker.get_positions()
    exposure = sum(abs(float(p["market_value"])) for p in positions)
    peak = float(db.get_state("peak_equity", str(account.equity)))
    drawdown = 0.0 if peak <= 0 else max(0.0, (peak - account.equity) / peak)
    day_start = float(db.get_state("day_start_equity", str(account.equity)))
    daily_pnl = account.equity - day_start
    return {
        "equity": account.equity,
        "drawdown": drawdown,
        "daily_pnl": daily_pnl,
        "exposure": exposure,
        "positions": positions,
        "mode": "live" if ensure_live_gate().allowed else "paper",
        "kill_switch": db.get_state("kill_switch", "false") == "true",
        "armed": db.get_state("armed_live", "false") == "true",
    }


@app.post("/api/run_once")
def run_once() -> dict:
    return runner.run_once()


@app.post("/api/kill_switch/enable")
def kill_enable() -> dict[str, str]:
    db.set_state("kill_switch", "true")
    return {"status": "enabled"}


@app.post("/api/kill_switch/disable")
def kill_disable() -> dict[str, str]:
    db.set_state("kill_switch", "false")
    return {"status": "disabled"}


@app.post("/api/arm_live")
def arm_live(phrase: str = Form(...)) -> JSONResponse:
    if phrase != "ARM LIVE TRADING":
        return JSONResponse(
            {"status": "error", "message": "Invalid arming phrase"},
            status_code=400,
        )
    db.set_state("armed_live", "true")
    return JSONResponse({"status": "armed"})


@app.post("/api/disarm_live")
def disarm_live() -> dict[str, str]:
    db.set_state("armed_live", "false")
    return {"status": "disarmed"}


@app.post("/api/strategy/{strategy_id}/promote")
def promote_strategy(strategy_id: int, mode: str = Form("paper")) -> JSONResponse:
    if mode in {"live", "canary"}:
        gate = ensure_live_gate()
        if not gate.allowed:
            return JSONResponse({"status": "blocked", "reasons": gate.reasons}, status_code=400)
    db.update_strategy_mode(strategy_id, mode)
    return JSONResponse({"status": "ok", "strategy_id": strategy_id, "mode": mode})


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    state = api_state()
    runs = db.list_runs(10)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "state": state, "runs": runs},
    )


@app.get("/chat", response_class=HTMLResponse)
def chat_get(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("chat.html", {"request": request, "response": None})


@app.post("/chat", response_class=HTMLResponse)
def chat_post(request: Request, prompt: str = Form(...)) -> HTMLResponse:
    response = llm_provider.chat(prompt)
    return templates.TemplateResponse("chat.html", {"request": request, "response": response})


@app.get("/strategies", response_class=HTMLResponse)
def strategies(request: Request) -> HTMLResponse:
    items = db.list_strategies()
    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": items})


@app.get("/runs", response_class=HTMLResponse)
def runs(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "runs.html",
        {"request": request, "runs": db.list_runs(), "risk_events": db.list_risk_events()},
    )


@app.get("/settings", response_class=HTMLResponse)
def settings_view(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "live_trading_env": settings.live_trading_env,
        "armed": db.get_state("armed_live", "false") == "true",
        "kill_switch": db.get_state("kill_switch", "false") == "true",
        "risk": {
            "max_drawdown": settings.max_drawdown_from_peak,
            "max_daily_loss": settings.max_daily_loss,
            "per_trade_risk": settings.per_trade_risk,
            "max_gross_exposure": settings.max_gross_exposure,
            "max_orders_per_hour": settings.max_orders_per_hour,
        },
    }
    return templates.TemplateResponse("settings.html", context)


@app.post("/actions/run_once")
def run_once_action() -> RedirectResponse:
    runner.run_once()
    return RedirectResponse(url="/runs", status_code=303)
