from __future__ import annotations

import logging

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes_calls import router as calls_router
from app.api.routes_orders import router as orders_router
from app.config import settings
from app.db import init_db
from app.services.menu import load_menu
from app.utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(calls_router)
app.include_router(orders_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    Path("./data").mkdir(parents=True, exist_ok=True)
    init_db()
    try:
        menu = load_menu(settings.menu_path)
    except Exception as exc:
        logger.error("Failed to load menu: %s", exc)
        menu = {"categories": []}
    app.state.menu = menu


@app.get("/")
def root() -> dict:
    return {"status": "ok", "app": settings.app_name}
