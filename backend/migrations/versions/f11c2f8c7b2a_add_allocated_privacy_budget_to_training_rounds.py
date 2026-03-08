"""Add allocated_privacy_budget to training_rounds

Revision ID: f11c2f8c7b2a
Revises: 397b211e348e
Create Date: 2026-03-04 09:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'f11c2f8c7b2a'
down_revision: Union[str, Sequence[str], None] = '397b211e348e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column['name'] for column in inspector.get_columns('training_rounds')}

    if 'allocated_privacy_budget' not in existing_columns:
        op.add_column(
            'training_rounds',
            sa.Column('allocated_privacy_budget', sa.Float(), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column['name'] for column in inspector.get_columns('training_rounds')}

    if 'allocated_privacy_budget' in existing_columns:
        op.drop_column('training_rounds', 'allocated_privacy_budget')
