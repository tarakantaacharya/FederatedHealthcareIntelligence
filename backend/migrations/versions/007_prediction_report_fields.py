"""
Phase B: Add prediction report fields

Revision ID: 007_prediction_report_fields
Revises: 006_dataset_intelligence
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_prediction_report_fields'
down_revision = '006_dataset_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    """Add prediction report columns"""
    with op.batch_alter_table('prediction_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('prediction_value', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('input_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('summary_text', sa.Text(), nullable=True))


def downgrade():
    """Remove prediction report columns"""
    with op.batch_alter_table('prediction_records', schema=None) as batch_op:
        batch_op.drop_column('summary_text')
        batch_op.drop_column('input_snapshot')
        batch_op.drop_column('prediction_value')
        batch_op.drop_column('prediction_timestamp')
