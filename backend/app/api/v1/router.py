from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    surveys,
    websocket,
)

router = APIRouter()

router.include_router(health.router)
router.include_router(surveys.router)
router.include_router(websocket.router)
