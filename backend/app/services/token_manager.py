"""
Token management for SF 311 OAuth tokens.
Handles both system-wide tokens (for guests) and per-user tokens.
"""
import json
import time
import logging
from typing import Optional
from sqlalchemy.orm import Session

# Import the reporter_lib auth module
import sys
from pathlib import Path
lib_path = Path(__file__).parent.parent.parent / "reporter_lib"
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

import auth

from ..core.config import settings
from ..models.system_config import SystemConfig
from ..models.user import User

logger = logging.getLogger(__name__)


SYSTEM_TOKEN_KEY = "sf311_system_token"


class TokenManager:
    """Manages SF 311 OAuth tokens for system and users."""
    
    @staticmethod
    def _acquire_new_token() -> dict:
        """
        Acquire a brand new token from SF 311 (no user interaction needed).
        Returns dict with access_token, refresh_token, expires_in, obtained_at.
        """
        logger.info("Acquiring new SF 311 token programmatically...")
        
        tokens = auth.acquire_tokens(
            base_url=settings.SF311_BASE_URL,
            client_id=settings.SF311_CLIENT_ID,
            redirect_uri=settings.SF311_REDIRECT_URI,
            scope=settings.SF311_SCOPE,
            identity_provider_id=None,
            user_agent_web="Alert311/1.0 Web",
            user_agent_app="Alert311/1.0",
            timeout=30,
        )
        
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_in": tokens.expires_in,
            "obtained_at": int(time.time()),
        }
    
    @staticmethod
    def _refresh_existing_token(refresh_token: str) -> dict:
        """
        Refresh an existing token using refresh_token.
        Returns dict with access_token, refresh_token, expires_in, obtained_at.
        """
        logger.info("Refreshing existing SF 311 token...")
        
        tokens = auth.refresh_tokens(
            base_url=settings.SF311_BASE_URL,
            client_id=settings.SF311_CLIENT_ID,
            redirect_uri=settings.SF311_REDIRECT_URI,
            scope=settings.SF311_SCOPE,
            refresh_token=refresh_token,
            user_agent_app="Alert311/1.0",
            timeout=30,
        )
        
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_in": tokens.expires_in,
            "obtained_at": int(time.time()),
        }
    
    @staticmethod
    async def ensure_system_token_exists(db: Session) -> None:
        """
        Ensure system token exists. Create one if it doesn't.
        Call this on app startup.
        """
        config = db.query(SystemConfig).filter(
            SystemConfig.key == SYSTEM_TOKEN_KEY
        ).first()
        
        if config:
            logger.info("System SF 311 token already exists")
            return
        
        logger.info("No system token found, acquiring initial token...")
        token_data = TokenManager._acquire_new_token()
        
        # Store in database
        config = SystemConfig(
            key=SYSTEM_TOKEN_KEY,
            value=json.dumps(token_data),
            last_updated_timestamp=token_data["obtained_at"],
        )
        db.add(config)
        db.commit()
        
        logger.info("✓ System SF 311 token created and stored")
    
    @staticmethod
    async def get_system_token(db: Session) -> str:
        """
        Get a valid system token (for guest users).
        Automatically refreshes if expired or near expiration.
        """
        config = db.query(SystemConfig).filter(
            SystemConfig.key == SYSTEM_TOKEN_KEY
        ).first()
        
        if not config:
            raise RuntimeError(
                "System token not found. Run ensure_system_token_exists() first."
            )
        
        token_data = json.loads(config.value)
        now = int(time.time())
        expires_at = token_data["obtained_at"] + token_data["expires_in"]
        
        # Refresh if expired or expiring within 5 minutes
        if now >= (expires_at - 300):
            logger.info("System token expired/expiring soon, refreshing...")
            try:
                new_token_data = TokenManager._refresh_existing_token(
                    token_data["refresh_token"]
                )
                
                # Update in database
                config.value = json.dumps(new_token_data)
                config.last_updated_timestamp = new_token_data["obtained_at"]
                db.commit()
                
                logger.info("✓ System token refreshed")
                return new_token_data["access_token"]
            except Exception as e:
                logger.error(f"Failed to refresh system token: {e}")
                # Try acquiring a brand new token as fallback
                logger.info("Attempting to acquire brand new token...")
                new_token_data = TokenManager._acquire_new_token()
                config.value = json.dumps(new_token_data)
                config.last_updated_timestamp = new_token_data["obtained_at"]
                db.commit()
                logger.info("✓ New system token acquired")
                return new_token_data["access_token"]
        
        return token_data["access_token"]
    
    @staticmethod
    async def get_user_token(user: User, db: Session) -> str:
        """
        Get a valid token for a specific user.
        Automatically refreshes if expired or near expiration.
        """
        if not user.sf311_access_token or not user.sf311_refresh_token:
            raise RuntimeError(
                f"User {user.phone} has no SF 311 tokens. "
                "They should be auto-assigned on phone verification."
            )
        
        now = int(time.time())
        
        # Refresh if expired or expiring within 5 minutes
        if user.sf311_token_expires_at and now >= (user.sf311_token_expires_at - 300):
            logger.info(f"User {user.phone} token expired/expiring, refreshing...")
            new_token_data = TokenManager._refresh_existing_token(
                user.sf311_refresh_token
            )
            
            # Update user's tokens
            user.sf311_access_token = new_token_data["access_token"]
            user.sf311_refresh_token = new_token_data["refresh_token"]
            user.sf311_token_expires_at = (
                new_token_data["obtained_at"] + new_token_data["expires_in"]
            )
            db.commit()
            
            logger.info(f"✓ User {user.phone} token refreshed")
            return new_token_data["access_token"]
        
        return user.sf311_access_token
    
    @staticmethod
    async def assign_token_to_user(user: User, db: Session) -> None:
        """
        Acquire a new token and assign it to a user.
        Call this when user verifies their phone number.
        """
        logger.info(f"Assigning SF 311 token to user {user.phone}...")
        
        token_data = TokenManager._acquire_new_token()
        
        user.sf311_access_token = token_data["access_token"]
        user.sf311_refresh_token = token_data["refresh_token"]
        user.sf311_token_expires_at = (
            token_data["obtained_at"] + token_data["expires_in"]
        )
        db.commit()
        
        logger.info(f"✓ Token assigned to user {user.phone}")
    
    @staticmethod
    async def refresh_system_token_proactively(db: Session) -> None:
        """
        Proactively refresh the system token.
        Call this from a cron job every 12 hours.
        """
        logger.info("Proactive system token refresh (cron job)...")
        
        config = db.query(SystemConfig).filter(
            SystemConfig.key == SYSTEM_TOKEN_KEY
        ).first()
        
        if not config:
            logger.warning("No system token to refresh, creating one...")
            await TokenManager.ensure_system_token_exists(db)
            return
        
        token_data = json.loads(config.value)
        
        try:
            new_token_data = TokenManager._refresh_existing_token(
                token_data["refresh_token"]
            )
            config.value = json.dumps(new_token_data)
            config.last_updated_timestamp = new_token_data["obtained_at"]
            db.commit()
            logger.info("✓ System token proactively refreshed")
        except Exception as e:
            logger.error(f"Proactive refresh failed: {e}")
            # Try acquiring a brand new token
            logger.info("Acquiring brand new token as fallback...")
            new_token_data = TokenManager._acquire_new_token()
            config.value = json.dumps(new_token_data)
            config.last_updated_timestamp = new_token_data["obtained_at"]
            db.commit()
            logger.info("✓ New system token acquired")
    
    @staticmethod
    async def refresh_user_tokens_proactively(db: Session) -> dict:
        """
        Proactively refresh all user tokens that expire within 24 hours.
        Call this from a cron job.
        Returns dict with success/failure counts.
        """
        logger.info("Proactive user token refresh (cron job)...")
        
        now = int(time.time())
        expiring_threshold = now + (24 * 3600)  # 24 hours from now
        
        # Find users with tokens expiring soon
        users = db.query(User).filter(
            User.verified == True,
            User.sf311_access_token.isnot(None),
            User.sf311_refresh_token.isnot(None),
            User.sf311_token_expires_at < expiring_threshold,
        ).all()
        
        logger.info(f"Found {len(users)} users with tokens expiring within 24h")
        
        success_count = 0
        failure_count = 0
        
        for user in users:
            try:
                new_token_data = TokenManager._refresh_existing_token(
                    user.sf311_refresh_token
                )
                user.sf311_access_token = new_token_data["access_token"]
                user.sf311_refresh_token = new_token_data["refresh_token"]
                user.sf311_token_expires_at = (
                    new_token_data["obtained_at"] + new_token_data["expires_in"]
                )
                db.commit()
                success_count += 1
                logger.info(f"✓ Refreshed token for user {user.phone}")
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user.phone}: {e}")
                failure_count += 1
        
        logger.info(
            f"Proactive user token refresh complete: "
            f"{success_count} succeeded, {failure_count} failed"
        )
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "total_users": len(users),
        }
