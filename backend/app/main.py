from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, passenger, queue, waiting
from app.services.prediction import prediction_service

# Initialize FastAPI app
app = FastAPI(
    title="Smart Airport Command Center API",
    description="AI-powered airport operations prediction system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event - Load ML models
@app.on_event("startup")
async def startup_event():
    """Load ML models on startup"""
    print("\n" + "="*60)
    print("🚀 Starting Smart Airport Command Center API")
    print("="*60)
    try:
        prediction_service.load_all_models()
        print("✅ All models loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Some models failed to load: {str(e)}")
    print("="*60 + "\n")

# Include API routers
app.include_router(health.router)
app.include_router(passenger.router)
app.include_router(queue.router)
app.include_router(waiting.router)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Smart Airport Command Center API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "passenger_flow": "/api/predict/passenger-flow",
            "queue_length": "/api/predict/queue-length",
            "waiting_time": "/api/predict/waiting-time"
        }
    } 