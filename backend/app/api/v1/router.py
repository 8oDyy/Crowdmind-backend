from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    datasets,
    models,
    agents,
    experiments,
    reactions,
    websocket,
)

router = APIRouter()

router.include_router(health.router)
router.include_router(datasets.router)
router.include_router(models.router)
router.include_router(agents.router)
router.include_router(experiments.router)
router.include_router(reactions.router)
router.include_router(websocket.router)
