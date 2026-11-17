from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    return {"message": "Inventory Intelligence API", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
