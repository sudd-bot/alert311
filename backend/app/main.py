"""
Alert311 FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid

from .core.config import settings
from .core.database import init_db
from .routes import auth, alerts, reports, cron, sf311_auth, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Alert311 API

    Automated SMS alerts when specific 311 reports are filed in San Francisco.

    ### Authentication
    Currently uses phone number as a simple identifier. Phone verification is required before creating alerts.

    ### Rate Limits
    - Twilio API: 1 verification code per 5 minutes per number
    - SF 311 API: Shared system token with automatic refresh

    ### Endpoints
    - **Auth**: Register and verify phone numbers
    - **Alerts**: Create, list, update, and delete alerts
    - **Reports**: Get nearby 311 reports and stored reports
    - **Health**: System health monitoring
    """,
    version="1.0.0",
    contact={
        "name": "Alert311",
        "url": "https://alert311-ui.vercel.app",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Middleware to add request ID for debugging and cache headers for performance
@app.middleware("http")
async def add_request_id_and_cache_headers(request: Request, call_next):
    """
    Add a unique request ID to each request for debugging and tracing.
    Add appropriate cache headers for GET requests to improve performance.
    """
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id

    # Add cache headers for GET requests
    # Safe caching strategy: short cache for dynamic data, longer for static data
    if request.method == "GET" and response.status_code == 200:
        path = request.url.path

        # Static / metadata endpoints - longer cache (5 minutes)
        if path in ["/", "/health", "/docs", "/openapi.json"]:
            response.headers["Cache-Control"] = "public, max-age=300"

        # Dynamic data endpoints - very short cache (30 seconds) to reduce duplicate requests
        # while keeping data relatively fresh
        elif path.startswith("/reports/nearby") or path.startswith("/alerts"):
            response.headers["Cache-Control"] = "public, max-age=30, s-maxage=60"

        # User-specific data - private cache (1 minute)
        elif path.startswith("/auth/me") or path.startswith("/alerts/") and path.count("/") == 3:
            response.headers["Cache-Control"] = "private, max-age=60"

    return response

# CORS middleware (for Next.js frontend)
# Restrict to actual frontend URLs in production
allowed_origins = [
    "https://alert311-ui.vercel.app",
    "https://www.alert311.com",  # For when custom domain is set up
    "http://localhost:3000",  # For local development
    "http://sudd.local:3000",  # For local development (custom hostname)
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
app.include_router(admin.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database and system tokens on startup."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Ensure system SF 311 token exists
        from .core.database import SessionLocal
        from .services.token_manager import TokenManager
        
        db = SessionLocal()
        try:
            await TokenManager.ensure_system_token_exists(db)
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
    Includes database connectivity and SF311 token availability.
    """
    from .core.database import SessionLocal
    from sqlalchemy import text
    from .services.token_manager import TokenManager
    from .models.system_config import SystemConfig

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

    # Check SF311 token availability (fast check - just verify config exists)
    sf311_status = "unknown"
    try:
        db = SessionLocal()
        from .services.token_manager import SYSTEM_TOKEN_KEY
        config = db.query(SystemConfig).filter(
            SystemConfig.key == SYSTEM_TOKEN_KEY
        ).first()
        db.close()
        sf311_status = "available" if config else "not_initialized"
    except Exception as e:
        logger.warning(f"SF311 token health check failed: {e}")
        sf311_status = "error"
        try:
            db.close()
        except:
            pass

    return {
        "status": "healthy",
        "database": db_status,
        "sf311_token": sf311_status
    }
