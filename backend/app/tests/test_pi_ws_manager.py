"""Tests for PiWsManager."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import WebSocketDisconnect

from app.core.errors import PiError
from app.infrastructure.pi.pi_ws_manager import PiWsManager


class FakeWS:
    """Minimal fake WebSocket driving PiWsManager.handle_connection."""

    def __init__(self) -> None:
        self._incoming: asyncio.Queue[str | None] = asyncio.Queue()
        self.sent: list[dict] = []
        self.accepted = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, msg: dict) -> None:
        self.sent.append(msg)

    async def receive_text(self) -> str:
        item = await self._incoming.get()
        if item is None:
            raise WebSocketDisconnect()
        return item

    async def push(self, text: str) -> None:
        await self._incoming.put(text)

    async def simulate_disconnect(self) -> None:
        await self._incoming.put(None)


async def _wait_connected(mgr: PiWsManager) -> None:
    for _ in range(50):
        if mgr.connected:
            return
        await asyncio.sleep(0.005)
    raise AssertionError("manager never connected")


async def test_call_roundtrip() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    async def replier() -> None:
        for _ in range(100):
            if ws.sent:
                break
            await asyncio.sleep(0.005)
        task_id = ws.sent[-1]["task_id"]
        await ws.push(json.dumps({"task_id": task_id, "result": {"ok": True}}))

    reply_task = asyncio.create_task(replier())
    result = await mgr.call("health", {"foo": "bar"}, timeout=2)
    await reply_task

    assert result == {"ok": True}
    assert ws.sent[-1]["type"] == "health"
    assert ws.sent[-1]["foo"] == "bar"

    await ws.simulate_disconnect()
    await handler
    assert not mgr.connected


async def test_call_raises_when_not_connected() -> None:
    mgr = PiWsManager()
    with pytest.raises(PiError, match="not connected"):
        await mgr.call("health", {})


async def test_call_times_out() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    with pytest.raises(PiError, match="timeout"):
        await mgr.call("health", {}, timeout=0.1)

    await ws.simulate_disconnect()
    await handler


async def test_pending_future_rejected_on_disconnect() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    call_task = asyncio.create_task(mgr.call("health", {}, timeout=5))
    for _ in range(100):
        if ws.sent:
            break
        await asyncio.sleep(0.005)
    assert ws.sent, "call never sent"

    await ws.simulate_disconnect()
    with pytest.raises(PiError, match="disconnected"):
        await call_task

    await handler
    assert not mgr.connected


async def test_pong_is_ignored() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    await ws.push(json.dumps({"type": "pong"}))
    await asyncio.sleep(0.02)
    assert mgr.connected

    await ws.simulate_disconnect()
    await handler


async def test_error_payload_raises_pi_error() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    async def replier() -> None:
        for _ in range(100):
            if ws.sent:
                break
            await asyncio.sleep(0.005)
        task_id = ws.sent[-1]["task_id"]
        await ws.push(json.dumps({"task_id": task_id, "error": "boom"}))

    asyncio.create_task(replier())
    with pytest.raises(PiError, match="boom"):
        await mgr.call("survey_text", {}, timeout=2)

    await ws.simulate_disconnect()
    await handler


async def test_unknown_task_id_is_ignored() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    await ws.push(json.dumps({"task_id": "unknown-id", "result": {}}))
    await asyncio.sleep(0.02)
    assert mgr.connected

    await ws.simulate_disconnect()
    await handler


async def test_malformed_json_is_ignored() -> None:
    mgr = PiWsManager()
    ws = FakeWS()
    handler = asyncio.create_task(mgr.handle_connection(ws))
    await _wait_connected(mgr)

    await ws.push("not json at all")
    await asyncio.sleep(0.02)
    assert mgr.connected

    await ws.simulate_disconnect()
    await handler
