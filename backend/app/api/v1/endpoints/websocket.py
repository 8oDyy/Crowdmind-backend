import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_realtime_service

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/experiments/{experiment_id}")
async def websocket_experiment(
    websocket: WebSocket,
    experiment_id: str,
) -> None:
    realtime = get_realtime_service()
    await realtime.connect(experiment_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        realtime.disconnect(experiment_id, websocket)
    except Exception:
        realtime.disconnect(experiment_id, websocket)
