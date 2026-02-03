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
    try:
        init_db()
    except Exception as e:
        # Log but don't fail - database might not be ready on cold start
        print(f"Database init warning: {e}")


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


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables."""
    import os
    
    # Look for relevant env vars
    relevant_keys = [
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 
        'TWILIO_VERIFY_SERVICE_SID', 'TWILIO_FROM_NUMBER',
        'CRON_SECRET',
        'DATABASE_URL', 'POSTGRES_URL',
        'VERCEL', 'VERCEL_ENV'
    ]
    
    found = {}
    for key in relevant_keys:
        value = os.environ.get(key)
        if value:
            # Mask the value but show it exists
            if len(value) > 8:
                found[key] = f"{value[:4]}...{value[-4:]}"
            else:
                found[key] = "***"
        else:
            found[key] = None
    
    # Check for any keys containing our keywords
    all_matching = {}
    for key in os.environ:
        if any(keyword in key.upper() for keyword in ['TWILIO', 'CRON', 'DATABASE', 'POSTGRES']):
            value = os.environ[key]
            if len(value) > 8:
                all_matching[key] = f"{value[:4]}...{value[-4:]}"
            else:
                all_matching[key] = "***"
    
    return {
        'status': 'ok',
        'message': 'Environment variable check',
        'specific_vars': found,
        'all_matching_vars': all_matching,
        'total_env_vars': len(os.environ),
        'settings_loaded': settings.APP_NAME
    }
