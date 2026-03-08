"""
Create training_round_schemas table

Revision ID: add_round_schemas
Revises: (previous revision)
Create Date: 2026-02-27

ARCHITECTURAL PURPOSE:
This migration creates the training_round_schemas table for federated training governance.

Central server uses this to lock:
- Target column
- Feature schema
- Model architecture
- Hyperparameters

Hospitals MUST validate against this schema before federated training.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'add_round_schemas'
down_revision = None  # Update this to your last migration ID
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
        sa.Column('feature_schema', mysql.JSON(), nullable=False),
        sa.Column('feature_types', mysql.JSON(), nullable=True),
        sa.Column('sequence_required', sa.Boolean(), default=False),
        sa.Column('lookback', sa.Integer(), nullable=True),
        sa.Column('horizon', sa.Integer(), nullable=True),
        sa.Column('model_hyperparameters', mysql.JSON(), nullable=True),
        sa.Column('validation_rules', mysql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['round_id'], ['training_rounds.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('round_id', name='uq_training_round_schemas_round_id')
    )
    
    # Create indexes
    op.create_index('idx_round_schema_round_id', 'training_round_schemas', ['round_id'])
    op.create_index('idx_round_schema_architecture', 'training_round_schemas', ['model_architecture'])
    
    print("[MIGRATION] Created training_round_schemas table with indexes")


def downgrade():
    """Drop training_round_schemas table."""
    op.drop_index('idx_round_schema_architecture', table_name='training_round_schemas')
    op.drop_index('idx_round_schema_round_id', table_name='training_round_schemas')
    op.drop_table('training_round_schemas')
    
    print("[MIGRATION] Dropped training_round_schemas table")
