from fastapi import APIRouter

from app.api.v1.schemas.common import HealthResponse
from app.core.dependencies import PiClientDep
from app.infrastructure.pi.pi_client import PiClientError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(pi: PiClientDep) -> HealthResponse:
    try:
        pi_health = pi.health()
        pi_status = pi_health.get("status", "ok")
    except PiClientError:
        pi_status = "unreachable"
    return HealthResponse(status="ok", pi_status=pi_status)
