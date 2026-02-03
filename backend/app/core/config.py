from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Alert311"
    DEBUG: bool = False
    
    # Database (Vercel uses POSTGRES_URL, allow fallback)
    DATABASE_URL: Optional[str] = None
    POSTGRES_URL: Optional[str] = None
    
    @property
    def db_url(self) -> str:
        """Get database URL from either DATABASE_URL or POSTGRES_URL."""
        return self.DATABASE_URL or self.POSTGRES_URL or ""
    
    # 311 API (SF Spotmobile)
    SF311_BASE_URL: str = "https://mobile311.sfgov.org"
    SF311_CLIENT_ID: str = "KLHhIUu56qWPHrYA16MUvxBXaJbPoAmKDbFjDFhe"
    SF311_REDIRECT_URI: str = "sf311://auth"
    SF311_SCOPE: str = "refresh_token read write openid"
    SF311_GRAPHQL_URL: str = "https://san-francisco2-production.spotmobile.net/graphql"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str  # For phone verification
    TWILIO_FROM_NUMBER: Optional[str] = None  # For sending SMS alerts
    
    # Report Types (hardcoded defaults, can expand later)
    DEFAULT_REPORT_TYPE_ID: str = Field(default="963f1454-7c22-43be-aacb-3f34ae5d0dc7")  # Parking on sidewalk
    DEFAULT_REPORT_TYPE_NAME: str = Field(default="Parking on Sidewalk")
    
    # Cron Job Auth (simple bearer token for Vercel Cron)
    CRON_SECRET: str
    
    class Config:
        # .env file is optional - will use environment variables if not present
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings - will use environment variables in production
settings = Settings()
