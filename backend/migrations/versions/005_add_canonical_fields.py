"""Add canonical_fields table for target column governance

Revision ID: 005_canonical_fields
Revises: 004_profile_criteria
Create Date: 2025-01-07 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_canonical_fields'
down_revision = '004_profile_criteria'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade: Create canonical_fields table."""
    op.create_table(
        'canonical_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('field_name')
    )
    op.create_index(op.f('ix_canonical_fields_id'), 'canonical_fields', ['id'], unique=False)
    op.create_index(op.f('ix_canonical_fields_field_name'), 'canonical_fields', ['field_name'], unique=True)


def downgrade() -> None:
    """Downgrade: Drop canonical_fields table."""
    op.drop_index(op.f('ix_canonical_fields_field_name'), 'canonical_fields')
    op.drop_index(op.f('ix_canonical_fields_id'), 'canonical_fields')
    op.drop_table('canonical_fields')
