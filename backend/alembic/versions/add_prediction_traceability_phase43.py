"""Add prediction traceability fields (Phase 43)

Revision ID: phase43_001
Revises: add_round_schemas
Create Date: 2026-03-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'phase43_001'
down_revision = 'add_round_schemas'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to prediction_records table (all nullable initially for non-breaking migration)
    op.add_column('prediction_records', sa.Column('model_type', sa.String(20), nullable=True))
    op.add_column('prediction_records', sa.Column('model_version', sa.String(100), nullable=True))
    op.add_column('prediction_records', sa.Column('feature_importance', sa.JSON(), nullable=True))
    op.add_column('prediction_records', sa.Column('confidence_interval', sa.JSON(), nullable=True))
    op.add_column('prediction_records', sa.Column('model_accuracy_snapshot', sa.JSON(), nullable=True))
    op.add_column('prediction_records', sa.Column('prediction_hash', sa.String(256), nullable=True))
    op.add_column('prediction_records', sa.Column('dp_epsilon_used', sa.Float(), nullable=True))
    op.add_column('prediction_records', sa.Column('aggregation_participants', sa.Integer(), nullable=True))
    op.add_column('prediction_records', sa.Column('blockchain_hash', sa.String(256), nullable=True))
    op.add_column('prediction_records', sa.Column('contribution_weight', sa.Float(), nullable=True))
    op.add_column('prediction_records', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for efficient querying
    op.create_index('idx_hospital_created', 'prediction_records', ['hospital_id', 'created_at'])
    op.create_index('idx_round_predictions', 'prediction_records', ['round_id', 'created_at'])
    op.create_index('idx_dataset_predictions', 'prediction_records', ['dataset_id', 'created_at'])
    op.create_index('idx_prediction_hash', 'prediction_records', ['prediction_hash'])


def downgrade():
    # Remove indexes
    op.drop_index('idx_prediction_hash', table_name='prediction_records')
    op.drop_index('idx_dataset_predictions', table_name='prediction_records')
    op.drop_index('idx_round_predictions', table_name='prediction_records')
    op.drop_index('idx_hospital_created', table_name='prediction_records')
    
    # Remove columns
    op.drop_column('prediction_records', 'updated_at')
    op.drop_column('prediction_records', 'contribution_weight')
    op.drop_column('prediction_records', 'blockchain_hash')
    op.drop_column('prediction_records', 'aggregation_participants')
    op.drop_column('prediction_records', 'dp_epsilon_used')
    op.drop_column('prediction_records', 'prediction_hash')
    op.drop_column('prediction_records', 'model_accuracy_snapshot')
    op.drop_column('prediction_records', 'confidence_interval')
    op.drop_column('prediction_records', 'feature_importance')
    op.drop_column('prediction_records', 'model_version')
    op.drop_column('prediction_records', 'model_type')
