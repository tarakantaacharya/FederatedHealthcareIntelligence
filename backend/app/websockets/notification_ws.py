"""
WebSocket notification manager (Phase 31)
Real-time notification streaming
"""
from fastapi import WebSocket
from typing import List, Dict
import json
import logging

logger = logging.getLogger(__name__)


class NotificationWebSocketManager:
    """Manages WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Map hospital_id -> list of WebSocket connections
        self.connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, hospital_id: int):
        """Connect a hospital's WebSocket"""
        await websocket.accept()
        
        if hospital_id not in self.connections:
            self.connections[hospital_id] = []
        
        self.connections[hospital_id].append(websocket)
        logger.info(f"Hospital {hospital_id} connected to notification stream")
    
    def disconnect(self, websocket: WebSocket, hospital_id: int):
        """Disconnect a hospital's WebSocket"""
        if hospital_id in self.connections:
            if websocket in self.connections[hospital_id]:
                self.connections[hospital_id].remove(websocket)
            
            # Clean up empty lists
            if len(self.connections[hospital_id]) == 0:
                del self.connections[hospital_id]
        
        logger.info(f"Hospital {hospital_id} disconnected from notification stream")
    
    async def broadcast_to_hospital(self, hospital_id: int, notification: dict):
        """
        Broadcast notification to specific hospital
        
        Args:
            hospital_id: Target hospital ID
            notification: Notification data dict
        """
        if hospital_id not in self.connections:
            return
        
        message = json.dumps(notification)
        dead_connections = []
        
        for websocket in self.connections[hospital_id]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send to websocket: {e}")
                dead_connections.append(websocket)
        
        # Remove dead connections
        for websocket in dead_connections:
            self.disconnect(websocket, hospital_id)
    
    async def broadcast_to_all(self, notification: dict):
        """Broadcast notification to all connected hospitals"""
        message = json.dumps(notification)
        
        for hospital_id, websockets in list(self.connections.items()):
            for websocket in websockets[:]:  # Copy to avoid modification during iteration
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send to websocket: {e}")
                    self.disconnect(websocket, hospital_id)


# Global manager instance
notification_ws_manager = NotificationWebSocketManager()
