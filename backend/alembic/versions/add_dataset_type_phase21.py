"""Add dataset_type column for dataset classification (Phase 21)

Revision ID: phase21_001
Revises: phase43_001
Create Date: 2026-03-02 10:00:00.000000

ARCHITECTURAL PURPOSE:
This migration adds dataset_type column to datasets table for classification of:
- TABULAR: Standard tabular data (random split, basic features)
- TIME_SERIES: Time series data (chronological split, lag features)

Auto-detection on upload:
- If "timestamp" column present -> TIME_SERIES
- Otherwise -> TABULAR
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phase21_001'
down_revision = 'phase43_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add dataset_type column to datasets table."""
    # Add new column with default='TABULAR' for backward compatibility
    op.add_column(
        'datasets',
        sa.Column('dataset_type', sa.String(20), nullable=False, server_default='TABULAR')
    )
    
    # Create index for efficient filtering
    op.create_index('idx_dataset_type', 'datasets', ['dataset_type'])
    
    # Add database constraint to ensure valid values
    op.execute("""
        ALTER TABLE datasets 
        ADD CONSTRAINT check_dataset_type 
        CHECK (dataset_type IN ('TABULAR', 'TIME_SERIES'))
    """)


def downgrade():
    """Remove dataset_type column from datasets table."""
    # Drop constraint and column
    op.execute("ALTER TABLE datasets DROP CONSTRAINT check_dataset_type")
    op.drop_index('idx_dataset_type', 'datasets')
    op.drop_column('datasets', 'dataset_type')
