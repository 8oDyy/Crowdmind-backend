from fastapi import FastAPI, WebSocket

app = FastAPI(
    title="CrowdMind API",
    version="1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.websocket("/ws/live")
async def ws_live(ws: WebSocket):
    await ws.accept()
    await ws.send_text("ws connected")
    while True:
        msg = await ws.receive_text()
        await ws.send_text(f"echo: {msg}")
