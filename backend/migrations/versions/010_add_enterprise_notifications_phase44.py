"""Add enterprise notification event fields (Phase 44)

Revision ID: 010_add_enterprise_notifications_phase44
Revises: 009_add_prediction_traceability_phase43
Create Date: 2026-03-01 13:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_enterprise_notifications_phase44'
down_revision = '009_add_prediction_traceability_phase43'
branch_labels = None
depends_on = None


def upgrade():
    # Role-aware recipient routing
    op.add_column('notifications', sa.Column('recipient_role', sa.String(length=20), nullable=True))
    op.add_column('notifications', sa.Column('recipient_hospital_id', sa.Integer(), nullable=True))

    # Event tracking and references
    op.add_column('notifications', sa.Column('event_type', sa.String(length=64), nullable=True))
    op.add_column('notifications', sa.Column('reference_id', sa.Integer(), nullable=True))
    op.add_column('notifications', sa.Column('reference_type', sa.String(length=50), nullable=True))
    op.add_column('notifications', sa.Column('redirect_url', sa.String(length=512), nullable=True))

    # Severity + SLA
    op.add_column('notifications', sa.Column('severity', sa.String(length=20), nullable=True))
    op.add_column('notifications', sa.Column('deadline', sa.DateTime(), nullable=True))
    op.add_column('notifications', sa.Column('acknowledged_at', sa.DateTime(), nullable=True))

    # Backfill defaults for existing rows
    op.execute("UPDATE notifications SET recipient_role = 'HOSPITAL' WHERE recipient_role IS NULL")
    op.execute("UPDATE notifications SET severity = 'INFO' WHERE severity IS NULL")

    # Indexes for role-aware querying
    op.create_index('idx_notifications_recipient_role', 'notifications', ['recipient_role'])
    op.create_index('idx_notifications_recipient_hospital_id', 'notifications', ['recipient_hospital_id'])
    op.create_index('idx_notifications_event_type', 'notifications', ['event_type'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])


def downgrade():
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_event_type', table_name='notifications')
    op.drop_index('idx_notifications_recipient_hospital_id', table_name='notifications')
    op.drop_index('idx_notifications_recipient_role', table_name='notifications')

    op.drop_column('notifications', 'acknowledged_at')
    op.drop_column('notifications', 'deadline')
    op.drop_column('notifications', 'severity')
    op.drop_column('notifications', 'redirect_url')
    op.drop_column('notifications', 'reference_type')
    op.drop_column('notifications', 'reference_id')
    op.drop_column('notifications', 'event_type')
    op.drop_column('notifications', 'recipient_hospital_id')
    op.drop_column('notifications', 'recipient_role')
