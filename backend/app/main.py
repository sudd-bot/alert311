"""
Alert311 FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import uuid
import time

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
    Add response time header for observability and performance monitoring.
    """
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    # Track request start time for response time measurement
    start_time = time.time()

    response = await call_next(request)

    # Add response time header (in milliseconds, rounded to 2 decimal places)
    response_time_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["x-request-id"] = request_id
    response.headers["x-response-time-ms"] = str(response_time_ms)

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
    Uses simplified checks to avoid connection pool issues in serverless environments.
    """
    from .core.database import get_db
    from sqlalchemy import text
    from .models.system_config import SystemConfig
    from .services.token_manager import SYSTEM_TOKEN_KEY
    from fastapi import Depends

    db_status = "unknown"
    sf311_status = "unknown"
    
    try:
        # Use a single database session for all checks (more efficient)
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check database connectivity
            db.execute(text("SELECT 1"))
            db_status = "connected"
            
            # Check SF311 token availability (fast check - just verify config exists)
            config = db.query(SystemConfig).filter(
                SystemConfig.key == SYSTEM_TOKEN_KEY
            ).first()
            sf311_status = "available" if config else "not_initialized"
            
        except Exception as inner_e:
            logger.warning(f"Health check query failed: {inner_e}")
            db_status = "error"
            sf311_status = "error"
        finally:
            # Ensure cleanup
            try:
                db_gen.close()
            except:
                pass
                
    except Exception as e:
        logger.warning(f"Health check failed to get db session: {e}")
        db_status = "disconnected"
        sf311_status = "error"

    return {
        "status": "healthy",
        "database": db_status,
        "sf311_token": sf311_status
    }
