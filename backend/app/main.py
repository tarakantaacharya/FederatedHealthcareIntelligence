"""
FastAPI Application Entry Point
Federated Healthcare Intelligence Platform
"""
import os
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.config import get_settings
from app.database import engine, Base, SessionLocal

# Initialize logger
logger = logging.getLogger(__name__)

# ✅ IMPORT ALL MODELS (registered with Base.metadata)
# NOTE: Schema evolution is now managed by Alembic migrations
from app.models.hospital import Hospital
from app.models.dataset import Dataset
from app.models.training_rounds import TrainingRound  # MOVED: Import BEFORE ModelWeights (fixes relationship resolution)
from app.models.training_round_schema import TrainingRoundSchema  # Phase: Federated schema governance
from app.models.model_weights import ModelWeights
from app.models.model_mask import ModelMask  # Phase 41: Governance enforcement
from app.models.round_allowed_hospital import RoundAllowedHospital  # Phase A-Pro: Round participation policies
from app.models.alerts import Alert
from app.models.schema_mappings import SchemaMapping
from app.models.schema_versions import SchemaVersion
from app.models.privacy_budget import PrivacyBudget
from app.models.model_governance import ModelGovernance
from app.models.admin import Admin
from app.models.notification import Notification  # Phase 31
from app.models.notification_preferences import NotificationPreference  # Phase 31
from app.models.model_registry import ModelRegistry  # Phase 34
from app.models.blockchain import Blockchain  # Phase 18
from app.models.prediction_record import PredictionRecord
from app.models.hospitals_profile import HospitalProfile
from app.models.canonical_field import CanonicalField
from app.routes import security

# ────────────────────────────────────────────────────────────────
# ROUTE IMPORTS (clean, unique)
# ────────────────────────────────────────────────────────────────
from app.routes import (
    auth,
    admin_auth,
    admin_metrics,
    admin,
    hospitals,
    hospital_profile,
    datasets,
    preprocessing,  # Dataset preprocessing pipeline
    training,
    aggregation,
    weights,
    model_updates,
    model_metadata,
    rounds,
    round_policy,  # Phase A-Pro: Participation policies
    round_schema,  # Phase 2B: Round schema governance
    canonical_fields,  # Phase 45: Target column governance
    schema,
    mapping,
    normalization,
    categories,
    dp,
    mpc,
    predictions,
    ml_predictions,  # STRICT SEPARATION: ML_REGRESSION single-point predictions
    tft_forecasts,   # STRICT SEPARATION: TFT multi-horizon forecasts
    scenarios,
    blockchain,
    model_hashing,
    dropout,
    scheduler,
    drift_detection,
    privacy_budget,
    explainability,
    benchmark,
    model_governance,
    results_intelligence,
    copilot,
    password_management,
    notifications,  # Phase 31
    monitoring,  # Phase 37
    privacy,  # Phase 42: Privacy Governance Panel
    pipeline,  # Phase 43: Data Pipeline Monitoring
    test_route,  # DEBUG: Test DELETE routes
    websocket,  # MANDATORY: WebSocket streaming
    dashboard  # Dashboard metrics for UI
)

# ────────────────────────────────────────────────────────────────
# WEBSOCKET IMPORTS (Phase 27)
# ────────────────────────────────────────────────────────────────
from app.websockets import router as websocket_router

# Load settings
settings = get_settings()

# ────────────────────────────────────────────────────────────────
# DATABASE SCHEMA MANAGEMENT
# ────────────────────────────────────────────────────────────────
# Schema is now managed by Alembic migrations (no runtime creation)
# To apply migrations: alembic upgrade head
# Create database tables on startup (SQLAlchemy ORM initialization)
Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized via SQLAlchemy metadata.create_all()")
print("[STARTUP] PASS Database schema managed by Alembic\n")

# Check password integrity on startup
from app.database_init import check_password_integrity
check_password_integrity()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Privacy-Preserving Federated Learning for Hospital Resource Forecasting"
)

# ────────────────────────────────────────────────────────────────
# SECURITY MIDDLEWARE (Phase 39)
# ────────────────────────────────────────────────────────────────
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# ────────────────────────────────────────────────────────────────
# OPTIONAL HTTPS REDIRECT
# ────────────────────────────────────────────────────────────────
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# ────────────────────────────────────────────────────────────────
# CORS
# ────────────────────────────────────────────────────────────────
default_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

configured_cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else []
allow_origins = list(dict.fromkeys(configured_cors_origins + default_cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────────────────────
# HEALTH CHECKS
# ────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Federated Healthcare Intelligence API",
        "version": settings.APP_VERSION,
        "status": "operational"
    }

# ────────────────────────────────────────────────────────────────
# DEBUG: OPTIONS PREFLIGHT HANDLER
# ────────────────────────────────────────────────────────────────
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    print(f"[DEBUG] OPTIONS preflight received for: /{full_path}")
    return {"status": "ok"}

@app.get("/health/deep")
async def deep_health_check():
    """
    Deep health check: database connectivity + table counts + storage paths.
    """
    health = {
        "status": "ok",
        "database": {
            "ok": False,
            "dialect": settings.DATABASE_URL.split("://", 1)[0],
            "counts": {},
            "error": None,
        },
        "storage": {
            "upload_dir": settings.UPLOAD_DIR,
            "model_dir": settings.MODEL_DIR,
            "upload_dir_exists": os.path.isdir(settings.UPLOAD_DIR),
            "model_dir_exists": os.path.isdir(settings.MODEL_DIR),
        },
    }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        with SessionLocal() as db:
            health["database"]["counts"] = {
                "admins": db.query(Admin).count(),
                "hospitals": db.query(Hospital).count(),
                "datasets": db.query(Dataset).count(),
                "model_weights": db.query(ModelWeights).count(),
                "training_rounds": db.query(TrainingRound).count(),
                "model_registry": db.query(ModelRegistry).count(),
            }

        health["database"]["ok"] = True
    except SQLAlchemyError as exc:
        health["status"] = "degraded"
        health["database"]["error"] = str(exc)
    except Exception as exc:
        health["status"] = "degraded"
        health["database"]["error"] = str(exc)

    if not health["storage"]["upload_dir_exists"] or not health["storage"]["model_dir_exists"]:
        health["status"] = "degraded"

    return health

# ────────────────────────────────────────────────────────────────
# ROUTERS
# ────────────────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_auth.router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_metrics.router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(hospital_profile.router, prefix="/api/hospital-profile", tags=["HospitalProfile"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["Hospitals"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(preprocessing.router, prefix="/api/preprocessing", tags=["Preprocessing"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(aggregation.router, prefix="/api/aggregation", tags=["Aggregation"])
app.include_router(weights.router, prefix="/api/weights", tags=["Weights"])
app.include_router(model_updates.router, prefix="/api/model-updates", tags=["Model Updates"])
app.include_router(model_metadata.router, prefix="/api", tags=["Model Metadata"])
app.include_router(rounds.router, prefix="/api/rounds", tags=["Federated Rounds"])
app.include_router(round_policy.router, prefix="/api/rounds", tags=["Round Policy"])  # Phase A-Pro
app.include_router(round_schema.router, tags=["Round Schema"])  # Phase 2B - uses /api prefix in router
app.include_router(canonical_fields.router, prefix="/api", tags=["Governance"])  # Phase 45
app.include_router(mapping.router, prefix="/api/mapping", tags=["Schema Mapping"])
app.add_api_route(
    "/api/auto-map/{dataset_id}",
    mapping.auto_map_dataset,
    methods=["POST"],
    tags=["Schema Mapping"],
)
app.include_router(normalization.router, prefix="/api/normalization", tags=["Normalization"])
app.add_api_route(
    "/api/normalize",
    normalization.normalize_dataset,
    methods=["POST"],
    tags=["Normalization"],
)
app.include_router(categories.router, prefix="/api/categories", tags=["Category Extensions"])
app.include_router(dp.router, prefix="/api/dp", tags=["Differential Privacy"])
app.include_router(mpc.router, prefix="/api/mpc", tags=["Secure MPC"])
app.include_router(test_route.router, prefix="/api/test", tags=["TEST"])  # DEBUG
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])  # Legacy - kept for backward compatibility
app.include_router(ml_predictions.router, prefix="/api/predictions", tags=["ML Predictions"])  # STRICT: ML_REGRESSION only
app.include_router(tft_forecasts.router, prefix="/api/predictions", tags=["TFT Forecasts"])  # STRICT: TFT only
app.include_router(scenarios.router, prefix="/api/scenarios", tags=["Scenario Analysis"])
app.include_router(blockchain.router, prefix="/api/blockchain", tags=["Blockchain"])
app.include_router(model_hashing.router, prefix="/api/model-hashing", tags=["Model Hashing"])
app.include_router(dropout.router, prefix="/api/dropout", tags=["Dropout Handling"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["Scheduler"])
app.include_router(drift_detection.router, prefix="/api/drift-detection", tags=["Drift Detection"])
app.include_router(privacy_budget.router, prefix="/api/privacy-budget", tags=["Privacy Budget"])
app.include_router(explainability.router, prefix="/api/explainability", tags=["Model Explainability"])
app.include_router(security.router, prefix="/api/security", tags=["Security"])
app.include_router(benchmark.router, prefix="/api/benchmark", tags=["Benchmarking"])
app.include_router(model_governance.router, prefix="/api/governance", tags=["Model Governance"])
app.include_router(results_intelligence.router, prefix="/api/results-intelligence", tags=["Results Intelligence"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Federated Copilot"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(password_management.router, prefix="/api/password", tags=["Password Management"])  # Phase 32
app.include_router(password_management.router, tags=["Password Management"])
app.include_router(notifications.router, tags=["Notifications"])  # Phase 31
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])  # Phase 37
app.include_router(privacy.router, tags=["Privacy Governance"])  # Phase 42
app.include_router(pipeline.router, tags=["Pipeline Monitoring"])  # Phase 43: Data Pipeline Visibility

# ────────────────────────────────────────────────────────────────
# WEBSOCKET ROUTERS (MANDATORY)
# ────────────────────────────────────────────────────────────────
app.include_router(websocket.router, prefix="/api", tags=["WebSocket"])

# ────────────────────────────────────────────────────────────────
# STARTUP EVENTS (Phase 27)
# ────────────────────────────────────────────────────────────────
import asyncio
from app.services.realtime_prediction_service import RealtimePredictionService
from app.services.canonical_field_service import CanonicalFieldService

@app.on_event("startup")
async def populate_canonical_fields():
    """Populate canonical fields on startup (idempotent)"""
    try:
        with SessionLocal() as db:
            CanonicalFieldService.populate_defaults(db)
            print("[STARTUP] PASS Canonical fields populated")
    except Exception as e:
        print(f"[STARTUP] ⚠ Failed to populate canonical fields: {e}")

@app.on_event("startup")
async def start_realtime_stream():
    """Start background task for real-time prediction streaming"""
    asyncio.create_task(RealtimePredictionService.stream_predictions())

# ────────────────────────────────────────────────────────────────
# DEVELOPMENT MODE ENTRYPOINT
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

