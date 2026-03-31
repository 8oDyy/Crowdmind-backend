"""Endpoint WebSocket pour le Pi worker.

Le Pi se connecte ici depuis son réseau local (connexion sortante).
Le backend lui envoie ensuite des tâches et récupère les résultats.
"""

from fastapi import APIRouter, WebSocket

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.pi.pi_ws_manager import get_pi_ws_manager

logger = get_logger(__name__)

router = APIRouter(tags=["pi-worker"])


@router.websocket("/ws/pi-worker")
async def pi_worker_ws(websocket: WebSocket) -> None:
    """Point de connexion WebSocket réservé au Pi worker.

    Authentification : si PI_TOKEN est configuré, le Pi doit
    fournir le token via :
      - Query param  : ?token=<token>
      - Header HTTP  : Authorization: Bearer <token>
    """
    settings = get_settings()

    if settings.PI_TOKEN:
        token = (
            websocket.query_params.get("token")
            or websocket.headers.get("authorization", "").removeprefix("Bearer ").strip()
        )
        if token != settings.PI_TOKEN:
            logger.warning("Pi worker rejected: invalid token")
            await websocket.close(code=4001)
            return

    manager = get_pi_ws_manager()
    await manager.handle_connection(websocket)
