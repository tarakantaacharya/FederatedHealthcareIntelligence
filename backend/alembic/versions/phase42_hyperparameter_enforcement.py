"""
Add Phase 42 Hyperparameter Enforcement and TFT Parameters

Revision ID: phase42_hyperparameter_enforcement
Revises: add_comprehensive_metrics
Create Date: 2026-03-05

ARCHITECTURAL PURPOSE:
Phase 42 implements:
1. Actual hyperparameter reporting from hospitals during weight upload
2. Hyperparameter compliance validation against federated contract
3. Extended TFT-specific hyperparameters (hidden_size, attention_heads, dropout, regularization)

Database Changes:
- ModelWeights: Add actual_hyperparameters (JSON), hyperparameter_compliant (Boolean)
- TrainingRound: Add tft_hidden_size, tft_attention_heads, tft_dropout, tft_regularization_factor
"""
from alembic import op
import sqlalchemy as sa


revision = 'phase42_hyperparameter_enforcement'
down_revision = 'add_comprehensive_metrics'
branch_labels = None
depends_on = None


def upgrade():
    """Add Phase 42 hyperparameter enforcement columns"""
    
    # Add columns to model_weights table
    op.add_column(
        'model_weights',
        sa.Column('actual_hyperparameters', sa.JSON(), nullable=True, comment='Actual hyperparameters used during training')
    )
    op.add_column(
        'model_weights',
        sa.Column('hyperparameter_compliant', sa.Boolean(), nullable=False, default=False, comment='Whether model complies with federated contract hyperparameters')
    )
    
    # Add columns to training_rounds table for TFT-specific hyperparameters
    op.add_column(
        'training_rounds',
        sa.Column('tft_hidden_size', sa.Integer(), nullable=True, comment='TFT hidden dimension for embedding')
    )
    op.add_column(
        'training_rounds',
        sa.Column('tft_attention_heads', sa.Integer(), nullable=True, comment='Number of attention heads in TFT')
    )
    op.add_column(
        'training_rounds',
        sa.Column('tft_dropout', sa.Float(), nullable=True, comment='Dropout rate for TFT (0.0-1.0)')
    )
    op.add_column(
        'training_rounds',
        sa.Column('tft_regularization_factor', sa.Float(), nullable=True, comment='L2 regularization factor for TFT')
    )


def downgrade():
    """Remove Phase 42 hyperparameter enforcement columns"""
    
    # Remove columns from training_rounds
    op.drop_column('training_rounds', 'tft_regularization_factor')
    op.drop_column('training_rounds', 'tft_dropout')
    op.drop_column('training_rounds', 'tft_attention_heads')
    op.drop_column('training_rounds', 'tft_hidden_size')
    
    # Remove columns from model_weights
    op.drop_column('model_weights', 'hyperparameter_compliant')
    op.drop_column('model_weights', 'actual_hyperparameters')
