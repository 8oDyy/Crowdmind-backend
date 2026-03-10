"""HTTP client for the CrowdMindAvis Raspberry Pi heuristic engine."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import PiError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PiClientError(PiError):
    """Raised when the Pi is unreachable or returns an error."""

    def __init__(self, message: str):
        super().__init__(message=message)


class PiClient:
    """Synchronous HTTP client for the Raspberry Pi API."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self._base_url = (base_url or settings.CROWDMIND_PI_URL).rstrip("/")
        self._timeout = timeout or settings.PI_TIMEOUT

    def health(self) -> dict[str, Any]:
        """Check Pi health: GET /health."""
        return self._get("/health")

    def survey_text(
        self,
        text: str,
        n_agents: int = 100,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Run a text survey on the Pi: POST /api/survey/text."""
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
        """Run a questionnaire survey on the Pi: POST /api/survey/questions."""
        return self._post(
            "/api/survey/questions",
            json={"questions": questions, "n_agents": n_agents, "seed": seed},
        )

    # ── Internal ──────────────────────────────────────────

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
