"""
WebSocket router for real-time streaming endpoints (Phase 27)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websockets.prediction_ws import prediction_ws_manager
from app.websockets.notification_ws import notification_ws_manager
from app.security.jwt import verify_ws_token

router = APIRouter()


@router.websocket("/ws/predictions")
async def prediction_stream(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time prediction streaming
    
    - **token**: JWT authentication token (query parameter)
    
    Streams prediction updates to authenticated clients every 5 seconds.
    """
    # Verify JWT token
    try:
        payload = verify_ws_token(token)
        hospital_id = payload.get("sub")
        if not hospital_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect client
    await prediction_ws_manager.connect(websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            await websocket.receive_text()  # Keep-alive ping
    except WebSocketDisconnect:
        prediction_ws_manager.disconnect(websocket)
    except Exception as e:
        prediction_ws_manager.disconnect(websocket)

@router.websocket("/ws/notifications")
async def notification_stream(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notification streaming (Phase 31)
    
    - **token**: JWT authentication token (query parameter)
    
    Streams notifications to authenticated hospital in real-time.
    """
    # Verify JWT token
    try:
        payload = verify_ws_token(token)
        hospital_id_str = payload.get("sub")
        if not hospital_id_str:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Extract hospital ID from database (assumes hospital_id is stored in token)
        # For simplicity, we'll use a hash of hospital_id_str as the integer ID
        # In production, query the database to get the actual integer ID
        import hashlib
        hospital_id = int(hashlib.md5(hospital_id_str.encode()).hexdigest()[:8], 16) % 1000000
        
    except Exception as e:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect client
    await notification_ws_manager.connect(websocket, hospital_id)
    
    try:
        # Keep connection alive
        while True:
            await websocket.receive_text()  # Keep-alive ping
    except WebSocketDisconnect:
        notification_ws_manager.disconnect(websocket, hospital_id)
    except Exception as e:
        notification_ws_manager.disconnect(websocket, hospital_id)