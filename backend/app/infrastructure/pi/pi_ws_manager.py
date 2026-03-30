"""Gestionnaire de la connexion WebSocket inverse du Pi.

Le Pi se connecte au backend (connexion sortante) et ce manager
gère le canal bidirectionnel pour envoyer des tâches et récupérer
les résultats de manière asynchrone.
"""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from app.core.errors import PiError
from app.core.logging import get_logger

logger = get_logger(__name__)


class PiWsManager:
    """Gère une connexion WebSocket unique depuis le Pi worker."""

    def __init__(self) -> None:
        self._ws: WebSocket | None = None
        self._pending: dict[str, asyncio.Future] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    # ── Configuration ─────────────────────────────────────

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Enregistre la boucle asyncio principale (appelé au startup)."""
        self._loop = loop

    @property
    def connected(self) -> bool:
        return self._ws is not None

    # ── Gestion de la connexion WebSocket ─────────────────

    async def handle_connection(self, ws: WebSocket) -> None:
        """Accepte et gère la connexion du Pi jusqu'à sa déconnexion."""
        await ws.accept()
        if self._ws is not None:
            logger.warning("Pi reconnected — replacing previous connection")
        self._ws = ws
        logger.info("Pi worker connected")

        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if msg.get("type") == "pong":
                    continue

                task_id = msg.get("task_id")
                if not task_id or task_id not in self._pending:
                    continue

                future = self._pending.pop(task_id)
                if future.done():
                    continue

                if "error" in msg:
                    future.set_exception(PiError(message=msg["error"]))
                else:
                    future.set_result(msg.get("result", {}))

        except WebSocketDisconnect:
            logger.warning("Pi worker disconnected")
        except Exception as exc:
            logger.error("Pi WS unexpected error: %s", exc)
        finally:
            self._ws = None
            # Résoudre toutes les futures en attente avec une erreur
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(PiError(message="Pi disconnected"))
            self._pending.clear()

    # ── Envoi de tâches ───────────────────────────────────

    async def call(
        self,
        task_type: str,
        payload: dict,
        timeout: float = 60.0,
    ) -> dict:
        """Envoie une tâche au Pi et attend la réponse (coroutine)."""
        if self._ws is None:
            raise PiError(message="Pi not connected via WebSocket")

        task_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._pending[task_id] = future

        try:
            await self._ws.send_json({"task_id": task_id, "type": task_type, **payload})
            return await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(task_id, None)
            if not future.done():
                future.cancel()
            raise PiError(message=f"Pi timeout after {timeout}s")
        except Exception:
            self._pending.pop(task_id, None)
            raise

    def call_sync(
        self,
        task_type: str,
        payload: dict,
        timeout: float = 60.0,
    ) -> dict:
        """Version synchrone — pour les endpoints sync FastAPI (thread pool).

        Utilise run_coroutine_threadsafe pour soumettre la coroutine
        à la boucle asyncio principale depuis un thread worker.
        """
        if self._loop is None or not self._loop.is_running():
            raise PiError(message="Pi event loop not available")

        future = asyncio.run_coroutine_threadsafe(
            self.call(task_type, payload, timeout),
            self._loop,
        )
        try:
            return future.result(timeout=timeout + 5)
        except TimeoutError:
            raise PiError(message=f"Pi sync timeout after {timeout + 5}s")


# ── Singleton ─────────────────────────────────────────────

_pi_ws_manager: PiWsManager | None = None


def get_pi_ws_manager() -> PiWsManager:
    global _pi_ws_manager
    if _pi_ws_manager is None:
        _pi_ws_manager = PiWsManager()
    return _pi_ws_manager
