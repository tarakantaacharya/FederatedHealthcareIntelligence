from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import Base and all models BEFORE setting target_metadata
from app.database import Base

# Import ALL models to ensure they're registered with Base.metadata
# CRITICAL: All models must be imported before target_metadata is set
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.training_rounds import TrainingRound
from app.models.model_weights import ModelWeights
from app.models.model_mask import ModelMask
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

# Now set target_metadata to Base.metadata (which has all models registered)
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
