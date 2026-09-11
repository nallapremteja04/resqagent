import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database.db import engine, Base, SessionLocal
import backend.models  # Ensures all 8 models are loaded
from backend.models.user import User
from backend.core.security import hash_password

# Create/verify database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResQAgent API",
    description="Agentic AI Emergency Response & Coordination System with Role-Based Authentication",
    version="1.1.0"
)

# Configure CORS for production (Vercel) and local development
raw_cors = os.getenv("CORS_ORIGINS", "")
frontend_url = os.getenv("FRONTEND_URL", "")

default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

allowed_origins = list(default_origins)
if frontend_url:
    clean_fe = frontend_url.strip().rstrip("/")
    if clean_fe and clean_fe not in allowed_origins:
        allowed_origins.append(clean_fe)
if raw_cors:
    for o in raw_cors.split(","):
        cleaned = o.strip().rstrip("/")
        if cleaned and cleaned not in allowed_origins:
            allowed_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def ensure_admin_exists():
    """
    Guarantees an initial administrator account exists in the database.
    Does NOT seed fake citizens or fake responders into production.
    """
    db = SessionLocal()
    try:
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count == 0:
            admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@resqagent.org").lower()
            admin_pwd = os.getenv("INITIAL_ADMIN_PASSWORD", "ResQAdmin2026!")
            admin_name = os.getenv("INITIAL_ADMIN_NAME", "System Administrator")
            
            admin_user = User(
                name=admin_name,
                email=admin_email,
                phone="+1-555-0000",
                password_hash=hash_password(admin_pwd),
                role="admin",
                location="Emergency Operations Command",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"[ResQAgent Security] Initial administrator account initialized: {admin_email}")
    finally:
        db.close()

@app.get("/health")
def root_health():
    """Minimal health check endpoint for Render service monitoring"""
    return {
        "status": "ok",
        "service": "resqagent-backend",
        "version": "1.1.0"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "ResQAgent Orchestrator",
        "auth_enabled": True,
        "version": "1.1.0"
    }

# Register API routers
from backend.api import (
    auth_routes,
    admin_routes,
    user_routes,
    responder_routes,
    incident_routes,
    assignment_routes,
    report_routes,
    simulation_routes,
)

app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
app.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
app.include_router(responder_routes.router, prefix="/api/responders", tags=["Responders"])
app.include_router(incident_routes.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(assignment_routes.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(report_routes.router, prefix="/api/reports", tags=["Reports"])
app.include_router(simulation_routes.router, prefix="/api/simulation", tags=["Simulation"])

# Mount static frontend files if directory exists
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
