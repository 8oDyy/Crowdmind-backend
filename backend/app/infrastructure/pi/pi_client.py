"""Client pour le Pi heuristic engine.

Priorité : connexion WebSocket inverse (Pi → backend) si disponible.
Fallback  : appel HTTP direct (CROWDMIND_PI_URL) si le Pi est accessible
            en réseau (utile en dev local).
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import PiError
from app.core.logging import get_logger
from app.infrastructure.pi.pi_ws_manager import PiWsManager, get_pi_ws_manager

logger = get_logger(__name__)


class PiClientError(PiError):
    def __init__(self, message: str):
        super().__init__(message=message)


class PiClient:
    """Client Pi — WebSocket si connecté, HTTP sinon."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._base_url = (base_url or settings.CROWDMIND_PI_URL).rstrip("/")
        self._timeout = timeout or settings.PI_TIMEOUT

    def _mgr(self) -> PiWsManager:
        return get_pi_ws_manager()

    # ── Interface publique (inchangée) ────────────────────

    def health(self) -> dict[str, Any]:
        mgr = self._mgr()
        if mgr.connected:
            return mgr.call_sync("health", {}, timeout=10.0)
        return self._get("/health")

    def survey_text(
        self,
        text: str,
        n_agents: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        mgr = self._mgr()
        if mgr.connected:
            return mgr.call_sync(
                "survey_text",
                {"text": text, "n_agents": n_agents, "seed": seed},
                timeout=self._timeout,
            )
        return self._post(
            "/api/survey/text",
            json={"text": text, "n_agents": n_agents, "seed": seed},
        )

    def survey_questions(
        self,
        questions: list[dict[str, Any]],
        n_agents: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        mgr = self._mgr()
        if mgr.connected:
            return mgr.call_sync(
                "survey_questions",
                {"questions": questions, "n_agents": n_agents, "seed": seed},
                timeout=self._timeout,
            )
        return self._post(
            "/api/survey/questions",
            json={"questions": questions, "n_agents": n_agents, "seed": seed},
        )

    # ── HTTP fallback ─────────────────────────────────────

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            resp = httpx.get(url, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            raise PiClientError(f"Pi unreachable at {url}")
        except httpx.HTTPStatusError as e:
            raise PiClientError(f"Pi returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise PiClientError(f"Pi request failed: {e}")

    def _post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            resp = httpx.post(url, json=json, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.ConnectError:
            raise PiClientError(f"Pi unreachable at {url}")
        except httpx.HTTPStatusError as e:
            raise PiClientError(f"Pi returned {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise PiClientError(f"Pi request failed: {e}")


# ── Singleton ─────────────────────────────────────────────

_pi_client: PiClient | None = None


def get_pi_client() -> PiClient:
    global _pi_client
    if _pi_client is None:
        _pi_client = PiClient()
    return _pi_client


def reset_pi_client() -> None:
    global _pi_client
    _pi_client = None
