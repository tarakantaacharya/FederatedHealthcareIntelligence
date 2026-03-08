"""
Benchmarking service for multi-hospital performance comparison (Phase 28)
Privacy-preserving aggregated metrics only
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from app.models.model_weights import ModelWeights
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound


class BenchmarkService:
    """Service for cross-hospital performance benchmarking"""
    
    @staticmethod
    def get_round_benchmarks(db: Session, round_number: int) -> List[Dict]:
        """
        Get performance benchmarks for a specific training round
        
        Args:
            db: Database session
            round_number: Training round number
        
        Returns:
            List of hospital performance metrics for the round
        """
        records = (
            db.query(
                Hospital.hospital_name,
                ModelWeights.local_accuracy,
                ModelWeights.local_loss,
                ModelWeights.round_number
            )
            .join(Hospital, Hospital.id == ModelWeights.hospital_id)
            .filter(
                ModelWeights.round_number == round_number,
                ModelWeights.is_global == False  # Only local hospital models
            )
            .all()
        )

        return [
            {
                "hospital": r.hospital_name,
                "accuracy": float(r.local_accuracy) if r.local_accuracy else None,
                "loss": float(r.local_loss) if r.local_loss else None,
                "round": r.round_number
            }
            for r in records
        ]
    
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10) -> List[Dict]:
        """
        Get global leaderboard of top-performing hospitals
        
        Args:
            db: Database session
            limit: Maximum number of results (default: 10)
        
        Returns:
            Ranked list of hospitals by average accuracy
        """
        # Get average accuracy per hospital across all rounds
        records = (
            db.query(
                Hospital.hospital_name,
                func.avg(ModelWeights.local_accuracy).label("avg_accuracy"),
                func.count(ModelWeights.id).label("num_models")
            )
            .join(Hospital, Hospital.id == ModelWeights.hospital_id)
            .filter(
                ModelWeights.is_global == False,
                ModelWeights.local_accuracy.isnot(None)
            )
            .group_by(Hospital.hospital_name)
            .order_by(func.avg(ModelWeights.local_accuracy).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "rank": idx + 1,
                "hospital": r.hospital_name,
                "avg_accuracy": float(r.avg_accuracy) if r.avg_accuracy else 0.0,
                "num_models": r.num_models
            }
            for idx, r in enumerate(records)
        ]
    
    @staticmethod
    def get_hospital_progress(db: Session, hospital_id: int) -> List[Dict]:
        """
        Get performance progression for a specific hospital across rounds
        
        Args:
            db: Database session
            hospital_id: Hospital ID
        
        Returns:
            List of performance metrics per round
        """
        records = (
            db.query(
                ModelWeights.round_number,
                ModelWeights.local_accuracy,
                ModelWeights.local_loss,
                ModelWeights.created_at
            )
            .filter(
                ModelWeights.hospital_id == hospital_id,
                ModelWeights.is_global == False
            )
            .order_by(ModelWeights.round_number.asc())
            .all()
        )

        return [
            {
                "round": r.round_number,
                "accuracy": float(r.local_accuracy) if r.local_accuracy else None,
                "loss": float(r.local_loss) if r.local_loss else None,
                "timestamp": str(r.created_at)
            }
            for r in records
        ]
    
    @staticmethod
    def get_round_statistics(db: Session, round_number: int) -> Dict:
        """
        Get aggregated statistics for a specific round
        
        Args:
            db: Database session
            round_number: Training round number
        
        Returns:
            Aggregated statistics (avg, min, max accuracy/loss)
        """
        stats = (
            db.query(
                func.avg(ModelWeights.local_accuracy).label("avg_accuracy"),
                func.min(ModelWeights.local_accuracy).label("min_accuracy"),
                func.max(ModelWeights.local_accuracy).label("max_accuracy"),
                func.avg(ModelWeights.local_loss).label("avg_loss"),
                func.min(ModelWeights.local_loss).label("min_loss"),
                func.max(ModelWeights.local_loss).label("max_loss"),
                func.count(ModelWeights.id).label("num_participants")
            )
            .filter(
                ModelWeights.round_number == round_number,
                ModelWeights.is_global == False
            )
            .first()
        )

        return {
            "round_number": round_number,
            "avg_accuracy": float(stats.avg_accuracy) if stats.avg_accuracy else None,
            "min_accuracy": float(stats.min_accuracy) if stats.min_accuracy else None,
            "max_accuracy": float(stats.max_accuracy) if stats.max_accuracy else None,
            "avg_loss": float(stats.avg_loss) if stats.avg_loss else None,
            "min_loss": float(stats.min_loss) if stats.min_loss else None,
            "max_loss": float(stats.max_loss) if stats.max_loss else None,
            "num_participants": stats.num_participants
        }
