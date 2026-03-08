"""
WebSocket connection manager for real-time predictions (Phase 27)
"""
from fastapi import WebSocket
from typing import List
import json


class PredictionConnectionManager:
    """Manages WebSocket connections for real-time prediction streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection from active list"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global singleton instance
prediction_ws_manager = PredictionConnectionManager()
