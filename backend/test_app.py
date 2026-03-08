"""Backend API - Minimal version for testing"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Federated Healthcare Intelligence API",
    version="1.0.0",
    description="Privacy-preserving federated learning platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Federated Healthcare API",
        "docs": "http://localhost:8000/docs",
        "api_version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
