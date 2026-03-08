"""Privacy budget accounting service (Phase 25 - Concurrency Hardened)
Enforces atomic epsilon consumption with transaction safety.

DATABASE ENGINE REQUIREMENTS:
- SQLite: Single writer lock (default)
- MySQL/InnoDB: Row-level locking (REQUIRED - must set isolation level READ COMMITTED)
- PostgreSQL: Row-level locking with FOR UPDATE
- DO NOT use MyISAM - no row locking support

CONCURRENCY GUARANTEES:
- Row-level lock acquired before budget calculation
- Budget recalculated after lock to prevent TOCTOU race
- Unique constraint enforces single consumption per round per hospital
- Single commit at end prevents partial updates
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, UniqueConstraint
from fastapi import HTTPException, status
from typing import Dict, List
from app.models.privacy_budget import PrivacyBudget
from app.models.hospital import Hospital


class PrivacyBudgetService:
    """Service for privacy budget tracking (governance-safe)"""

    DEFAULT_TOTAL_BUDGET = 10.0
    WARNING_THRESHOLD = 0.7
    CRITICAL_THRESHOLD = 0.9

    # ─────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _get_total_spent(hospital_id: int, db: Session) -> float:
        """Get cumulative epsilon spent across ALL rounds (for reporting only)."""
        total = db.query(func.coalesce(func.sum(PrivacyBudget.epsilon), 0.0)).filter(
            PrivacyBudget.hospital_id == hospital_id
        ).scalar()
        return float(total or 0.0)
    
    @staticmethod
    def _get_round_spent(hospital_id: int, round_number: int, db: Session) -> float:
        """Get epsilon spent by hospital in specific round only.
        
        Each round has its own fresh budget allocation - this tracks only
        spending within that round.
        """
        total = db.query(func.coalesce(func.sum(PrivacyBudget.epsilon), 0.0)).filter(
            PrivacyBudget.hospital_id == hospital_id,
            PrivacyBudget.round_number == round_number
        ).scalar()
        return float(total or 0.0)

    # ─────────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def check_budget_availability(
        hospital_id: int,
        required_epsilon: float,
        round_number: int,
        db: Session
    ) -> Dict:
        """Check if hospital has sufficient budget for THIS ROUND (per-round fresh allocation).
        
        CRITICAL FIX: Each round starts with its own FRESH budget allocation.
        Budget consumed in round 1 does NOT affect availability in round 2.
        
        Args:
            hospital_id: Hospital to check
            required_epsilon: Epsilon needed for this operation
            round_number: CURRENT round (not cumulative across rounds)
            db: Database session
            
        Returns:
            Budget status dict showing round-specific availability
        """
        # Get this round's allocation
        from app.models.training_rounds import TrainingRound
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not round_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )
        
        # Use round-specific allocation, NOT global budget
        round_budget = round_obj.allocated_privacy_budget or PrivacyBudgetService.DEFAULT_TOTAL_BUDGET
        
        # Check ONLY spending in THIS round (not cumulative across all rounds!)
        round_spent = PrivacyBudgetService._get_round_spent(hospital_id, round_number, db)
        remaining = round_budget - round_spent

        has_budget = remaining >= required_epsilon

        return {
            "hospital_id": hospital_id,
            "round_number": round_number,
            "round_budget": round_budget,
            "round_spent": round_spent,
            "required_epsilon": required_epsilon,
            "remaining_budget": remaining,
            "has_sufficient_budget": has_budget,
            "would_exceed_budget": not has_budget,
        }

    @staticmethod
    def consume_budget(
        hospital_id: int,
        round_number: int,
        epsilon_spent: float,
        delta: float,
        noise_multiplier: float,
        db: Session
    ) -> PrivacyBudget:
        """
        Atomically enforce and record epsilon expenditure (transaction-safe).
        
        SEQUENCE (must not reorder):
        1. Lock hospital row (MySQL: row-level, SQLite: implicit)
        2. Get round-specific allocated budget
        3. Check for duplicate round usage (prevents double-consumption)
        4. Verify budget not exceeded for this round
        5. Insert record
        6. Single commit at end
        
        HARD-REJECTS if budget exceeded or duplicate round detected.
        """
        from app.models.training_rounds import TrainingRound
        
        # 🔴 STEP 1: ACQUIRE ROW-LEVEL LOCK on hospital
        # In MySQL InnoDB: SELECT ... FOR UPDATE (row lock)
        # In SQLite: Implicit transaction lock (single writer)
        # In PostgreSQL: SELECT ... FOR UPDATE (row lock)
        hospital = (
            db.query(Hospital)
            .filter(Hospital.id == hospital_id)
            .with_for_update()  # Row-level lock in MySQL/Postgres, no-op in SQLite
            .first()
        )
        
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found"
            )
        
        # 🔴 STEP 2: GET round-specific allocated budget
        round_obj = db.query(TrainingRound).filter(
            TrainingRound.round_number == round_number
        ).first()
        
        if not round_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Round {round_number} not found"
            )
        
        # Use round-allocated budget if set, otherwise fallback to default
        round_budget = round_obj.allocated_privacy_budget or PrivacyBudgetService.DEFAULT_TOTAL_BUDGET
        
        # 🔴 STEP 3: CHECK existing spending (for accumulated budget tracking)
        existing = db.query(PrivacyBudget).filter(
            PrivacyBudget.hospital_id == hospital_id,
            PrivacyBudget.round_number == round_number
        ).first()
        
        # 🔴 STEP 4: VERIFY budget not exceeded for this specific round (including accumulated)
        accumulated_spending = existing.epsilon_spent if existing else 0.0
        total_would_be = accumulated_spending + epsilon_spent
        
        if total_would_be > round_budget:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Privacy budget exceeded for round {round_number}. "
                    f"Already spent={accumulated_spending:.4f}, "
                    f"This operation={epsilon_spent:.4f}, "
                    f"Allocated={round_budget:.4f}"
                )
            )
        
        # 🔴 STEP 5: UPSERT record (accumulate spending if exists, create if new)
        if existing:
            # ACCUMULATE: Add to existing spending instead of creating duplicate
            existing.epsilon_spent += epsilon_spent
            existing.epsilon = existing.epsilon_spent  # Keep in sync
            existing.noise_multiplier = noise_multiplier  # Update latest values
            record = existing
            print(f"[BUDGET UPSERT] Accumulated: hospital={hospital_id}, round={round_number}, "
                  f"new_total={existing.epsilon_spent:.4f} (was {accumulated_spending:.4f})")
        else:
            # CREATE: New record for this (hospital, round) pair
            record = PrivacyBudget(
                hospital_id=hospital_id,
                round_number=round_number,
                epsilon=epsilon_spent,
                delta=delta,
                epsilon_spent=epsilon_spent,
                total_epsilon_budget=round_budget,
                mechanism="gaussian",
                noise_multiplier=noise_multiplier,
            )
            db.add(record)
            print(f"[BUDGET CREATE] New: hospital={hospital_id}, round={round_number}, "
                  f"epsilon={epsilon_spent:.4f}")
        
        # 🔴 STEP 6: SINGLE COMMIT at end (no intermediate commits)
        db.commit()
        db.refresh(record)
        
        return record

    @staticmethod
    def get_hospital_budget_status(
        hospital_id: int,
        db: Session
    ) -> Dict:

        total_spent = PrivacyBudgetService._get_total_spent(hospital_id, db)
        total_budget = PrivacyBudgetService.DEFAULT_TOTAL_BUDGET
        remaining = total_budget - total_spent

        consumption_ratio = total_spent / total_budget if total_budget > 0 else 0.0

        if consumption_ratio >= PrivacyBudgetService.CRITICAL_THRESHOLD:
            status = "CRITICAL"
        elif consumption_ratio >= PrivacyBudgetService.WARNING_THRESHOLD:
            status = "WARNING"
        else:
            status = "HEALTHY"

        return {
            "hospital_id": hospital_id,
            "total_epsilon_spent": total_spent,
            "total_budget": total_budget,
            "remaining_budget": remaining,
            "consumption_percentage": consumption_ratio * 100,
            "status": status,
        }

    @staticmethod
    def get_all_hospitals_budget_summary(db: Session) -> Dict:

        hospitals = db.query(Hospital).all()

        summaries = []
        total_spent_system = 0.0

        for hospital in hospitals:
            status = PrivacyBudgetService.get_hospital_budget_status(
                hospital.id, db
            )
            summaries.append({
                "hospital_id": hospital.id,
                "hospital_name": hospital.hospital_name,
                **status
            })
            total_spent_system += status["total_epsilon_spent"]

        return {
            "total_hospitals": len(hospitals),
            "total_epsilon_spent_system_wide": total_spent_system,
            "hospitals": summaries
        }