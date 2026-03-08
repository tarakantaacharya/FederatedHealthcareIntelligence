"""Add round policy configuration fields

Revision ID: 003_round_policy
Revises: 092ec1d2afe3
Create Date: 2026-02-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_round_policy'
down_revision = '092ec1d2afe3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema: add selection_criteria and selection_value to training_rounds"""
    op.add_column('training_rounds', sa.Column('selection_criteria', sa.String(50), nullable=True))
    op.add_column('training_rounds', sa.Column('selection_value', sa.String(100), nullable=True))


def downgrade() -> None:
    """Downgrade schema: remove selection_criteria and selection_value from training_rounds"""
    op.drop_column('training_rounds', 'selection_value')
    op.drop_column('training_rounds', 'selection_criteria')
