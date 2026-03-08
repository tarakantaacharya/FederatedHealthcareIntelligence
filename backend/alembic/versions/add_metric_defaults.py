"""
Add default values to metric columns in model_weights table

Revision ID: add_metric_defaults
Revises: add_comprehensive_metrics
Create Date: 2026-03-06

ARCHITECTURAL PURPOSE:
This migration adds default values to all metric columns in model_weights to prevent NULL values:
- All error metrics default to 0.0
- This eliminates N/A displays in the frontend
- Ensures all new records have valid metrics even if not explicitly set
- Improves data consistency and query reliability
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_metric_defaults'
down_revision = 'add_comprehensive_metrics'  # Update to your latest migration ID
branch_labels = None
depends_on = None


def upgrade():
    """Add default values to metric columns"""
    # MySQL-specific syntax to add default values
    # Note: We use raw SQL because Alembic's alter_column has issues with MySQL defaults
    
    metric_columns = [
        'local_mae',
        'local_mse',
        'local_rmse',
        'local_adjusted_r2',
        'local_smape',
        'local_wape',
        'local_mase',
        'local_rmsle',
        'local_mape',
        'local_r2',
    ]
    
    # For each metric column, modify to have default value of 0.0
    for col in metric_columns:
        op.execute(
            f"ALTER TABLE model_weights MODIFY COLUMN {col} FLOAT DEFAULT 0.0"
        )
    
    print(f"✅ Added default values (0.0) to {len(metric_columns)} metric columns")


def downgrade():
    """Remove default values from metric columns"""
    metric_columns = [
        'local_mae',
        'local_mse',
        'local_rmse',
        'local_adjusted_r2',
        'local_smape',
        'local_wape',
        'local_mase',
        'local_rmsle',
        'local_mape',
        'local_r2',
    ]
    
    # Revert to no default
    for col in metric_columns:
        op.execute(
            f"ALTER TABLE model_weights MODIFY COLUMN {col} FLOAT"
        )
    
    print(f"✅ Removed default values from {len(metric_columns)} metric columns")
