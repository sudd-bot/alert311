from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Alert311"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    
    # 311 API (SF Spotmobile)
    SF311_BASE_URL: str = "https://mobile311.sfgov.org"
    SF311_CLIENT_ID: str = "KLHhIUu56qWPHrYA16MUvxBXaJbPoAmKDbFjDFhe"
    SF311_REDIRECT_URI: str = "sf311://auth"
    SF311_SCOPE: str = "refresh_token read write openid"
    SF311_GRAPHQL_URL: str = "https://mobile311.sfgov.org/api/graphql"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str  # For phone verification
    TWILIO_FROM_NUMBER: Optional[str] = None  # For sending SMS alerts
    
    # Report Types (can expand later)
    DEFAULT_REPORT_TYPE_ID: str = "963f1454-7c22-43be-aacb-3f34ae5d0dc7"  # Parking on sidewalk
    DEFAULT_REPORT_TYPE_NAME: str = "Parking on Sidewalk"
    
    # Cron Job Auth (simple bearer token for Vercel Cron)
    CRON_SECRET: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
