"""
Minimal working FastAPI app without database initialization 
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

# Create app
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "Federated Healthcare API"}

# Import routes AFTER app is created
from app.routes import auth, admin_auth, hospitals, datasets, training, weights, rounds

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_auth.router, prefix="/api/admin-auth", tags=["admin-auth"])
app.include_router(hospitals.router, prefix="/api/hospitals", tags=["hospitals"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(weights.router, prefix="/api/weights", tags=["weights"])
app.include_router(rounds.router, prefix="/api/rounds", tags=["rounds"])

print("FastAPI app started successfully!")
