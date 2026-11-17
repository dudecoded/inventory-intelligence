from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/status", tags=["health"])
def api_status() -> dict[str, str]:
    return {"status": "available", "version": "v1"}
