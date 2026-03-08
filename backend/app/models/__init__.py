"""
Models package initialization
Ensures all models are imported in correct order for SQLAlchemy relationships
"""

# Import base model classes first
from app.models.hospital import Hospital
from app.models.dataset import Dataset

# Import training round BEFORE model_weights (relationship dependency)
from app.models.training_rounds import TrainingRound, RoundStatus
from app.models.training_round_schema import TrainingRoundSchema

# Import model_weights AFTER training_rounds
from app.models.model_weights import ModelWeights
from app.models.model_mask import ModelMask

# Import other models
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.models.alerts import Alert
from app.models.schema_mappings import SchemaMapping
from app.models.schema_versions import SchemaVersion
from app.models.privacy_budget import PrivacyBudget
from app.models.model_governance import ModelGovernance
from app.models.admin import Admin
from app.models.notification import Notification
from app.models.notification_preferences import NotificationPreference
from app.models.model_registry import ModelRegistry
from app.models.blockchain import Blockchain
from app.models.prediction_record import PredictionRecord
from app.models.hospitals_profile import HospitalProfile
from app.models.canonical_field import CanonicalField

__all__ = [
    'Hospital',
    'Dataset',
    'TrainingRound',
    'RoundStatus',
    'TrainingRoundSchema',
    'ModelWeights',
    'ModelMask',
    'RoundAllowedHospital',
    'Alert',
    'SchemaMapping',
    'SchemaVersion',
    'PrivacyBudget',
    'ModelGovernance',
    'Admin',
    'Notification',
    'NotificationPreference',
    'ModelRegistry',
    'Blockchain',
    'PredictionRecord',
    'HospitalProfile',
    'CanonicalField',
]
