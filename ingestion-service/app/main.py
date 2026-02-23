from fastapi import FastAPI
from app.db import create_db_and_tables
from app.routers import items
from app.models import (
    Hotel,
    HotelEventModel,
    Subscription,
    HotelMeasure,
    MetricItem,
)

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

app = FastAPI(title="Ingestion ecostars", version="1.0.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(items.router)

@app.get("/health")
def health():
    return {"status": "ok"}