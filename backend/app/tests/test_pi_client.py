"""Tests for PiClient (WebSocket-only)."""

from __future__ import annotations

import pytest

from app.infrastructure.pi import pi_client as pi_client_module
from app.infrastructure.pi.pi_client import PiClient, PiClientError
from app.infrastructure.pi.pi_ws_manager import PiWsManager


@pytest.fixture
def disconnected_manager(monkeypatch: pytest.MonkeyPatch) -> PiWsManager:
    """Replace the global PiWsManager with a fresh one that has no Pi attached."""
    fresh = PiWsManager()
    monkeypatch.setattr(pi_client_module, "get_pi_ws_manager", lambda: fresh)
    return fresh


def test_health_raises_when_no_pi_connected(disconnected_manager: PiWsManager) -> None:
    client = PiClient()
    with pytest.raises(PiClientError, match="not connected"):
        client.health()


def test_survey_text_raises_when_no_pi_connected(disconnected_manager: PiWsManager) -> None:
    client = PiClient()
    with pytest.raises(PiClientError, match="not connected"):
        client.survey_text("foo", n_agents=1, seed=1)


def test_survey_questions_raises_when_no_pi_connected(disconnected_manager: PiWsManager) -> None:
    client = PiClient()
    with pytest.raises(PiClientError, match="not connected"):
        client.survey_questions(
            [{"id": "q1", "type": "stance", "text": "x"}],
            n_agents=1,
            seed=1,
        )


def test_timeout_defaults_to_settings_value() -> None:
    from app.core.config import get_settings

    client = PiClient()
    assert client._timeout == get_settings().PI_TIMEOUT


def test_timeout_override() -> None:
    client = PiClient(timeout=7.5)
    assert client._timeout == 7.5
