import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class RealtimeService:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, experiment_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if experiment_id not in self._connections:
            self._connections[experiment_id] = []
        self._connections[experiment_id].append(websocket)

    def disconnect(self, experiment_id: str, websocket: WebSocket) -> None:
        if experiment_id in self._connections:
            if websocket in self._connections[experiment_id]:
                self._connections[experiment_id].remove(websocket)
            if not self._connections[experiment_id]:
                del self._connections[experiment_id]

    async def broadcast(
        self,
        experiment_id: str,
        event_type: str,
        data: dict[str, Any],
    ) -> None:
        if experiment_id not in self._connections:
            return

        message = json.dumps({
            "type": event_type,
            "data": data,
            "ts": datetime.utcnow().isoformat(),
        })

        dead_connections: list[WebSocket] = []
        for websocket in self._connections[experiment_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                dead_connections.append(websocket)

        for ws in dead_connections:
            self.disconnect(experiment_id, ws)

    def get_connection_count(self, experiment_id: str) -> int:
        return len(self._connections.get(experiment_id, []))
