from __future__ import annotations

from fastapi import FastAPI

from pet_report.api.routes import router
from pet_report.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Pet Report Structuring Service",
    description="Open-source model based pet lab report structuring and interpretation service",
    version="1.0.0",
)
app.include_router(router)
