"""
Phase B: Add dataset intelligence tracking columns

Revision ID: 006_dataset_intelligence
Revises: 005_canonical_fields
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '006_dataset_intelligence'
down_revision = '005_canonical_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add dataset intelligence tracking columns"""
    # Add dataset intelligence columns
    with op.batch_alter_table('datasets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('times_trained', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('times_federated', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('last_trained_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('involved_rounds', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('last_training_type', sa.String(length=20), nullable=True))
    
    # Update existing records to have default values
    op.execute("UPDATE datasets SET times_trained = 0 WHERE times_trained IS NULL")
    op.execute("UPDATE datasets SET times_federated = 0 WHERE times_federated IS NULL")


def downgrade():
    """Remove dataset intelligence tracking columns"""
    with op.batch_alter_table('datasets', schema=None) as batch_op:
        batch_op.drop_column('last_training_type')
        batch_op.drop_column('involved_rounds')
        batch_op.drop_column('last_trained_at')
        batch_op.drop_column('times_federated')
        batch_op.drop_column('times_trained')
