"""
Alert311 FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .core.config import settings
from .core.database import init_db
from .routes import auth, alerts, reports, cron, sf311_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Automated 311 alerts via SMS",
    version="1.0.0",
)

# CORS middleware (for Next.js frontend)
# Restrict to actual frontend URLs in production
allowed_origins = [
    "https://alert311-ui.vercel.app",
    "https://www.alert311.com",  # For when custom domain is set up
    "http://localhost:3000",  # For local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    """Initialize database and system tokens on startup."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Ensure system SF 311 token exists
        from .core.database import SessionLocal
        from .services.token_manager import token_manager
        
        db = SessionLocal()
        try:
            await token_manager.ensure_system_token_exists(db)
            logger.info("System SF 311 token initialized")
        except Exception as e:
            logger.warning(f"SF 311 token initialization warning: {e}")
        finally:
            db.close()
            
    except Exception as e:
        # Log but don't fail - database might not be ready on cold start
        logger.warning(f"Startup initialization warning: {e}")
        logger.info("Application will continue, database will retry on first request")


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
    """
    Health check for monitoring.
    Includes database connectivity check.
    """
    from .core.database import SessionLocal
    from sqlalchemy import text
    
    db_status = "unknown"
    try:
        # Try to connect to database
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "database": db_status
    }
