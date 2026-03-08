"""
Real-time prediction streaming service (Phase 27)
Background task for broadcasting live prediction updates
"""
import asyncio
from typing import Dict, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.prediction_service import PredictionService
from app.services.round_service import RoundService
from app.websockets.prediction_ws import prediction_ws_manager
from app.config import get_settings
from app.models.model_weights import ModelWeights
from app.models.training_rounds import TrainingRound

settings = get_settings()


class RealtimePredictionService:
    """Service for streaming real-time prediction updates via WebSocket"""
    
    @staticmethod
    async def stream_predictions():
        """
        Background task that streams prediction updates every 5 seconds
        
        Broadcasts:
        - Latest global model predictions
        - Current round statistics
        - System status
        """
        # Create dedicated database session for background task
        engine = create_engine(settings.DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        
        while True:
            try:
                db = SessionLocal()
                
                # Get latest global model
                latest_global = db.query(ModelWeights).filter(
                    ModelWeights.is_global == True
                ).order_by(ModelWeights.round_number.desc()).first()
                
                # Get latest training round
                latest_round = db.query(TrainingRound).order_by(
                    TrainingRound.round_number.desc()
                ).first()
                
                # Prepare broadcast message
                message = {
                    "type": "prediction_update",
                    "timestamp": str(asyncio.get_event_loop().time()),
                    "data": {
                        "global_model": {
                            "id": latest_global.id if latest_global else None,
                            "round_number": latest_global.round_number if latest_global else 0,
                            "model_type": latest_global.model_type if latest_global else None,
                            "created_at": str(latest_global.created_at) if latest_global else None
                        } if latest_global else None,
                        "current_round": {
                            "round_number": latest_round.round_number if latest_round else 0,
                            "status": latest_round.status if latest_round else "N/A",
                            "num_participating_hospitals": latest_round.num_participating_hospitals if latest_round else 0,
                            "average_loss": latest_round.average_loss if latest_round else None,
                            "started_at": str(latest_round.started_at) if latest_round else None,
                            "completed_at": str(latest_round.completed_at) if latest_round else None
                        } if latest_round else None,
                        "system_status": "operational",
                        "active_connections": len(prediction_ws_manager.active_connections)
                    }
                }
                
                # Broadcast to all connected clients
                if prediction_ws_manager.active_connections:
                    await prediction_ws_manager.broadcast(message)
                
                db.close()
                
            except Exception as e:
                print(f"[RealtimePredictionService] Error: {str(e)}")
            
            # Wait 5 seconds before next broadcast
            await asyncio.sleep(5)
    
    @staticmethod
    async def stream_alert_updates():
        """
        Future enhancement: Stream alert updates
        Can be implemented in subsequent phases
        """
        pass
