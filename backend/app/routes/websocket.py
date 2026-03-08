"""
WebSocket streaming route (MANDATORY requirement #6)
Real-time updates for predictions and aggregation events
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
import asyncio
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time streaming
    
    MANDATORY: Broadcasts updates after:
    - Federated round completion
    - New predictions generated
    - Model updates available
    """
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, hospital_id: str):
        """Accept WebSocket connection for hospital"""
        await websocket.accept()
        
        if hospital_id not in self.active_connections:
            self.active_connections[hospital_id] = []
        
        self.active_connections[hospital_id].append(websocket)
        
        # Send welcome message
        await websocket.send_json({
            'type': 'connection',
            'status': 'connected',
            'hospital_id': hospital_id,
            'timestamp': datetime.now().isoformat(),
            'message': 'WebSocket connection established'
        })
    
    def disconnect(self, websocket: WebSocket, hospital_id: str):
        """Remove WebSocket connection"""
        if hospital_id in self.active_connections:
            if websocket in self.active_connections[hospital_id]:
                self.active_connections[hospital_id].remove(websocket)
            
            # Clean up empty lists
            if not self.active_connections[hospital_id]:
                del self.active_connections[hospital_id]
    
    async def broadcast_to_hospital(self, hospital_id: str, message: dict):
        """Send message to all connections for a hospital"""
        if hospital_id not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[hospital_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected websockets
        for conn in disconnected:
            self.disconnect(conn, hospital_id)
    
    async def broadcast_to_all(self, message: dict):
        """Send message to all active connections"""
        for hospital_id in list(self.active_connections.keys()):
            await self.broadcast_to_hospital(hospital_id, message)
    
    async def send_prediction_update(self, hospital_id: str, prediction_data: dict):
        """
        MANDATORY: Broadcast prediction update
        
        Args:
            hospital_id: Target hospital
            prediction_data: Prediction results with 3-horizon format
        """
        message = {
            'type': 'prediction_update',
            'timestamp': datetime.now().isoformat(),
            'data': prediction_data
        }
        await self.broadcast_to_hospital(hospital_id, message)
    
    async def send_aggregation_complete(self, round_number: int, details: dict):
        """
        MANDATORY: Broadcast aggregation completion
        
        Args:
            round_number: Completed round number
            details: Aggregation results (model_hash, num_hospitals, etc.)
        """
        message = {
            'type': 'aggregation_complete',
            'round_number': round_number,
            'timestamp': datetime.now().isoformat(),
            'data': details
        }
        await self.broadcast_to_all(message)
    
    async def send_model_update(self, round_number: int, global_model_id: int):
        """
        MANDATORY: Broadcast global model availability
        
        Args:
            round_number: Round number
            global_model_id: Global model ID
        """
        message = {
            'type': 'model_update',
            'round_number': round_number,
            'global_model_id': global_model_id,
            'timestamp': datetime.now().isoformat(),
            'message': f'Global model available for round {round_number}'
        }
        await self.broadcast_to_all(message)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/{hospital_id}")
async def websocket_endpoint(websocket: WebSocket, hospital_id: str):
    """
    WebSocket endpoint for real-time updates
    
    MANDATORY: Streams updates for:
    - New predictions (3-horizon)
    - Aggregation completion
    - Global model availability
    
    Usage (frontend):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/ws/HOSPITAL-001');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'prediction_update') {
            // Update dashboard
        } else if (data.type === 'aggregation_complete') {
            // Show aggregation complete notification
        }
    };
    ```
    
    Args:
        websocket: WebSocket connection
        hospital_id: Hospital identifier
    """
    await manager.connect(websocket, hospital_id)
    
    try:
        while True:
            # Keep connection alive and receive client messages
            data = await websocket.receive_text()
            
            # Echo back as heartbeat
            await websocket.send_json({
                'type': 'heartbeat',
                'timestamp': datetime.now().isoformat(),
                'received': data
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, hospital_id)
        print(f"WebSocket disconnected: {hospital_id}")
    
    except Exception as e:
        print(f"WebSocket error for {hospital_id}: {str(e)}")
        manager.disconnect(websocket, hospital_id)


# Export manager for use in other services
__all__ = ['router', 'manager']
