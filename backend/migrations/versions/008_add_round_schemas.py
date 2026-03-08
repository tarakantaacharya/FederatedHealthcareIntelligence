"""
Create training_round_schemas table for federated governance

Revision ID: 008_add_round_schemas
Revises: 007_prediction_report_fields
Create Date: 2026-02-27

ARCHITECTURAL PURPOSE:
This migration creates the training_round_schemas table for federated training governance.

Central server uses this to lock:
- Target column
- Feature schema (ordered list)
- Model architecture (ML_REGRESSION or TFT)
- Hyperparameters

Hospitals MUST validate their datasets against this schema before federated training.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '008_add_round_schemas'
down_revision = '007_prediction_report_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Create training_round_schemas table."""
    op.create_table(
        'training_round_schemas',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('round_id', sa.Integer(), nullable=False),
        sa.Column('model_architecture', sa.String(50), nullable=False),
        sa.Column('target_column', sa.String(100), nullable=False),
        sa.Column('feature_schema', sa.JSON(), nullable=False, comment='Ordered list of required feature names'),
        sa.Column('feature_types', sa.JSON(), nullable=True, comment='Mapping of feature names to expected data types'),
        sa.Column('sequence_required', sa.Boolean(), default=False, comment='True for TFT, False for ML'),
        sa.Column('lookback', sa.Integer(), nullable=True, comment='TFT encoder length'),
        sa.Column('horizon', sa.Integer(), nullable=True, comment='TFT prediction horizon'),
        sa.Column('model_hyperparameters', sa.JSON(), nullable=True, comment='Locked hyperparameters'),
        sa.Column('validation_rules', sa.JSON(), nullable=True, comment='min_samples, max_missing_rate, etc.'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['round_id'], ['training_rounds.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('round_id', name='uq_training_round_schemas_round_id')
    )
    
    # Create indexes for faster lookups
    op.create_index('idx_round_schema_round_id', 'training_round_schemas', ['round_id'])
    op.create_index('idx_round_schema_architecture', 'training_round_schemas', ['model_architecture'])


def downgrade():
    """Drop training_round_schemas table."""
    op.drop_index('idx_round_schema_architecture', table_name='training_round_schemas')
    op.drop_index('idx_round_schema_round_id', table_name='training_round_schemas')
    op.drop_table('training_round_schemas')
