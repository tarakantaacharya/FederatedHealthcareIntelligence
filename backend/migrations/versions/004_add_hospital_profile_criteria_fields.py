"""Add size_category and experience_level to hospital profile for selection criteria

Revision ID: 004_profile_criteria
Revises: 003_round_policy
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_profile_criteria'
down_revision = '003_round_policy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: Add size_category and experience_level columns to hospitals_profile."""
    op.add_column(
        'hospitals_profile',
        sa.Column('size_category', sa.String(50), nullable=True)
    )
    op.add_column(
        'hospitals_profile',
        sa.Column('experience_level', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    """Downgrade: Remove size_category and experience_level columns from hospitals_profile."""
    op.drop_column('hospitals_profile', 'experience_level')
    op.drop_column('hospitals_profile', 'size_category')
