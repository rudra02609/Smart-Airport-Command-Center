"""
Smart Airport Command Center - Main FastAPI Application.
Registers all routers, middleware, and startup events.
"""

import sys
# Configure UTF-8 encoding for standard output on Windows to avoid UnicodeEncodeError
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api import health, passenger, queue, waiting
from app.api import alerts as alerts_api
from app.api import security_api
from app.cybersecurity.auth import router as auth_router

# Import services
from app.services.prediction import prediction_service

# Import middleware
from app.cybersecurity.middleware import RateLimitMiddleware, SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # --- Startup ---
    print("\n" + "="*60)
    print("🚀 Starting Smart Airport Command Center API v2.0")
    print("="*60)
    try:
        prediction_service.load_all_models()
        print("✅ All ML models loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Some models failed to load: {str(e)}")
    
    print("🔐 Cybersecurity layer active: RBAC, JWT, Audit, Anomaly Detection")
    print("🛡️  Rate limiting enabled")
    print("📊 Smart alerts and recommendations ready")
    print("="*60 + "\n")
    
    yield
    
    # --- Shutdown ---
    print("\n🛑 Shutting down Smart Airport Command Center API")


# Initialize FastAPI app
app = FastAPI(
    title="Smart Airport Command Center API",
    description="AI-powered airport operations prediction system with cybersecurity layer",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================
# MIDDLEWARE (order matters - first added = outermost)
# ============================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# ============================================================
# ROUTERS
# ============================================================

# Health (no auth required)
app.include_router(health.router)

# Authentication
app.include_router(auth_router)

# Prediction endpoints (auth required)
app.include_router(passenger.router)
app.include_router(queue.router)
app.include_router(waiting.router)

# Alerts & Analysis (auth required)
app.include_router(alerts_api.router)

# Security (admin only)
app.include_router(security_api.router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint with API overview."""
    return {
        "message": "Welcome to Smart Airport Command Center API",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "GET /api/health",
            "login": "POST /api/auth/login",
            "current_user": "GET /api/auth/me",
            "passenger_flow": "POST /api/predict/passenger-flow",
            "queue_length": "POST /api/predict/queue-length",
            "waiting_time": "POST /api/predict/waiting-time",
            "full_analysis": "POST /api/alerts/check",
            "evaluate_alerts": "POST /api/alerts/evaluate",
            "security_status": "GET /api/security/status",
            "audit_logs": "GET /api/security/logs",
            "anomaly_check": "POST /api/security/check"
        }
    }