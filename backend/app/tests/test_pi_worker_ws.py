"""Tests for the /ws/pi-worker WebSocket endpoint (auth)."""

from __future__ import annotations

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_accepts_when_no_token_configured(client: TestClient) -> None:
    with client.websocket_connect("/api/v1/ws/pi-worker"):
        pass  # handshake accepted, close cleanly


def test_rejects_missing_token_when_required(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "PI_TOKEN", "secret")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws/pi-worker") as ws:
            ws.receive_text()


def test_rejects_wrong_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "PI_TOKEN", "secret")
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/ws/pi-worker?token=wrong") as ws:
            ws.receive_text()


def test_accepts_valid_token_query_param(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "PI_TOKEN", "secret")
    with client.websocket_connect("/api/v1/ws/pi-worker?token=secret"):
        pass


def test_accepts_valid_token_bearer_header(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "PI_TOKEN", "secret")
    with client.websocket_connect(
        "/api/v1/ws/pi-worker",
        headers={"Authorization": "Bearer secret"},
    ):
        pass
