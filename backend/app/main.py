"""
Alert311 FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db
from .routes import auth, alerts, reports, cron, sf311_auth

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Automated 311 alerts via SMS",
    version="1.0.0",
)

# CORS middleware (for Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to actual frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(cron.router)
app.include_router(sf311_auth.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "healthy"}
