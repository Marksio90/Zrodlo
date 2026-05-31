"""WebSocket endpoint dla powiadomień real-time."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.auth import decode_token
from app.ws.manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Access token JWT"),
):
    """
    WebSocket dla powiadomień real-time.
    Połącz się z: ws://host/ws?token=<access_token>
    Wiadomości JSON: {"type": "notification", "data": {...}}
    """
    try:
        claims = decode_token(token)
        user_id = claims.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        # Wyślij potwierdzenie połączenia
        import json
        await websocket.send_text(json.dumps({"type": "connected", "user_id": user_id}))

        # Trzymaj połączenie otwarte (klient wysyła pingi lub czeka na zdarzenia)
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except WebSocketDisconnect:
                break
    finally:
        await ws_manager.disconnect(user_id, websocket)
