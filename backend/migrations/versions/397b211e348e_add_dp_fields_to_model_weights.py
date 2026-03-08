"""add dp fields to model_weights

Revision ID: 397b211e348e
Revises: 010_add_enterprise_notifications_phase44
Create Date: 2026-03-03 04:09:05.512479
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '397b211e348e'
down_revision: Union[str, Sequence[str], None] = '010_add_enterprise_notifications_phase44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (SQLite-safe minimal migration)."""

    # ─────────────────────────────────────────────
    # Add DP fields to model_weights
    # ─────────────────────────────────────────────
    op.add_column(
        'model_weights',
        sa.Column('epsilon_spent', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('delta', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('clip_norm', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('noise_multiplier', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('dp_mode', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('policy_snapshot', sa.JSON(), nullable=True)
    )

    # ─────────────────────────────────────────────
    # Add model_type to training_rounds
    # ─────────────────────────────────────────────
    op.add_column(
        'training_rounds',
        sa.Column(
            'model_type',
            sa.String(length=20),
            nullable=False,
            server_default='TFT'  # important for SQLite
        )
    )


def downgrade() -> None:
    """Downgrade schema (minimal rollback)."""

    op.drop_column('training_rounds', 'model_type')

    op.drop_column('model_weights', 'policy_snapshot')
    op.drop_column('model_weights', 'dp_mode')
    op.drop_column('model_weights', 'noise_multiplier')
    op.drop_column('model_weights', 'clip_norm')
    op.drop_column('model_weights', 'delta')
    op.drop_column('model_weights', 'epsilon_spent')