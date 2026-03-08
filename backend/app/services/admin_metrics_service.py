"""
Admin metrics service
Centralized aggregation of dashboard statistics
"""
from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.model_weights import ModelWeights


class AdminMetricsService:
    """Compute admin dashboard metrics from the database."""

    @staticmethod
    def get_admin_metrics(db: Session) -> dict:
        total_hospitals = db.query(Hospital).count()
        approved_hospitals = db.query(Hospital).filter(Hospital.is_verified == True).count()
        pending_approvals = db.query(Hospital).filter(Hospital.is_verified == False).count()

        active_rounds = db.query(TrainingRound).filter(
            TrainingRound.status == RoundStatus.TRAINING
        ).count()

        total_aggregations = db.query(ModelWeights).filter(
            ModelWeights.is_global == True,
            ModelWeights.hospital_id == None
        ).count()
        
        # Average global loss (from completed rounds)
        round_losses = db.query(TrainingRound).filter(
            TrainingRound.average_loss != None
        ).all()
        loss_values = [r.average_loss for r in round_losses if r.average_loss is not None]
        avg_global_loss = sum(loss_values) / len(loss_values) if loss_values else None
        
        # Participation heatmap (per round)
        heatmap = db.query(TrainingRound).order_by(TrainingRound.round_number.asc()).all()
        participation_heatmap = [
            {
                "round_number": r.round_number,
                "participants": r.num_participating_hospitals or 0,
                "status": r.status.value if hasattr(r.status, 'value') else r.status
            }
            for r in heatmap
        ]

        return {
            "total_hospitals": total_hospitals,
            "approved_hospitals": approved_hospitals,
            "pending_approvals": pending_approvals,
            "active_rounds": active_rounds,
            "total_aggregations": total_aggregations,
            "average_global_loss": avg_global_loss,
            "participation_heatmap": participation_heatmap
        }
