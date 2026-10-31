from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.api import admin, public
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Property
from app.services.geojson_import import import_geojson_file
from app.services.seed import seed_defaults
from app.services.sync import run_property_sync

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def scheduled_sync() -> None:
    db = SessionLocal()
    try:
        run_property_sync(db)
    finally:
        db.close()


def bootstrap_properties_if_empty() -> None:
    """Populate the map on first boot from GeoJSON and/or a live Warsaw sync."""
    db = SessionLocal()
    try:
        count = db.scalar(select(func.count()).select_from(Property)) or 0
        if count > 0:
            return

        candidates = [
            Path("/data/warsaw_properties.geojson"),
            Path("/app/warsaw_properties.geojson"),
            Path(__file__).resolve().parents[2] / "warsaw_properties.geojson",
        ]
        geojson_path = next((path for path in candidates if path.exists()), None)
        if geojson_path is not None:
            logger.info("Importing bootstrap GeoJSON from %s", geojson_path)
            import_geojson_file(db, geojson_path)

        count = db.scalar(select(func.count()).select_from(Property)) or 0
        if count == 0:
            logger.info("No local GeoJSON found; starting live Warsaw property sync")
            run_property_sync(db)
    except Exception:  # noqa: BLE001
        logger.exception("Initial property bootstrap failed")
    finally:
        db.close()


def scheduled_retention() -> None:
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import select

    from app.models import Suggestion

    settings = get_settings()
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
        old = list(db.scalars(select(Suggestion).where(Suggestion.created_at < cutoff)).all())
        for row in old:
            db.delete(row)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()

    if settings.environment != "test":
        Thread(target=bootstrap_properties_if_empty, daemon=True, name="bootstrap-sync").start()
        scheduler.add_job(
            scheduled_sync,
            "cron",
            hour=settings.sync_cron_hour,
            minute=settings.sync_cron_minute,
            id="daily_property_sync",
            replace_existing=True,
        )
        scheduler.add_job(
            scheduled_retention,
            "cron",
            hour=4,
            minute=15,
            id="daily_retention",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(public.router)
    app.include_router(admin.router)
    return app


app = create_app()
