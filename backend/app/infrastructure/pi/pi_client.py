"""Client pour le Pi heuristic engine (WebSocket uniquement).

Le Pi se connecte au backend via /api/v1/ws/pi-worker ; toutes les
demandes passent par PiWsManager. Si aucun Pi n'est connecté, les
appels lèvent PiClientError immédiatement.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.errors import PiError
from app.core.logging import get_logger
from app.infrastructure.pi.pi_ws_manager import PiWsManager, get_pi_ws_manager

logger = get_logger(__name__)


class PiClientError(PiError):
    pass


class PiClient:
    def __init__(self, timeout: float | None = None) -> None:
        settings = get_settings()
        self._timeout = timeout if timeout is not None else settings.PI_TIMEOUT

    def _require_connected(self) -> PiWsManager:
        mgr = get_pi_ws_manager()
        if not mgr.connected:
            raise PiClientError("Pi not connected via WebSocket")
        return mgr

    def health(self) -> dict[str, Any]:
        return self._require_connected().call_sync("health", {}, timeout=10.0)

    def survey_text(
        self,
        text: str,
        n_agents: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        return self._require_connected().call_sync(
            "survey_text",
            {"text": text, "n_agents": n_agents, "seed": seed},
            timeout=self._timeout,
        )

    def survey_questions(
        self,
        questions: list[dict[str, Any]],
        n_agents: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        return self._require_connected().call_sync(
            "survey_questions",
            {"questions": questions, "n_agents": n_agents, "seed": seed},
            timeout=self._timeout,
        )


_pi_client: PiClient | None = None


def get_pi_client() -> PiClient:
    global _pi_client
    if _pi_client is None:
        _pi_client = PiClient()
    return _pi_client


def reset_pi_client() -> None:
    global _pi_client
    _pi_client = None
