"""
Add 10 comprehensive metrics columns to model_weights table

Revision ID: add_comprehensive_metrics
Revises: Previous revision (update this based on latest migration)
Create Date: 2026-03-04

ARCHITECTURAL PURPOSE:
This migration adds all 10 regression metrics to model_weights for:
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)
- RMSE (Root Mean Squared Error)
- R² (Coefficient of Determination)
- Adjusted R² (adjusted for features)
- MAPE (Mean Absolute Percentage Error)
- sMAPE (Symmetric MAPE)
- WAPE (Weighted Absolute Percentage Error)
- MASE (Mean Absolute Scaled Error)
- RMSLE (Root Mean Squared Logarithmic Error)

These metrics enable:
1. Direct querying of model performance without parsing JSON
2. Better indexing for metric-based sorting/filtering
3. Compatibility with new TrainingResponse schema
4. Support for /api/training/status/{model_id} endpoint
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_comprehensive_metrics'
down_revision = None  # Update to your latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Add comprehensive metrics columns to model_weights"""
    # Add new metric columns (all nullable for backward compatibility)
    op.add_column(
        'model_weights',
        sa.Column('local_mae', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_mse', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_adjusted_r2', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_smape', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_wape', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_mase', sa.Float(), nullable=True)
    )
    op.add_column(
        'model_weights',
        sa.Column('local_rmsle', sa.Float(), nullable=True)
    )


def downgrade():
    """Remove the comprehensive metrics columns"""
    op.drop_column('model_weights', 'local_mae')
    op.drop_column('model_weights', 'local_mse')
    op.drop_column('model_weights', 'local_adjusted_r2')
    op.drop_column('model_weights', 'local_smape')
    op.drop_column('model_weights', 'local_wape')
    op.drop_column('model_weights', 'local_mase')
    op.drop_column('model_weights', 'local_rmsle')
