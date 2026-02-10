"""
Admin routes for manual operations.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from ..core.database import get_db
from ..models import SystemConfig

router = APIRouter(prefix="/admin", tags=["admin"])


class SetTokenRequest(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    obtained_at: int


@router.post("/set-system-token")
async def set_system_token(token_data: SetTokenRequest, db: Session = Depends(get_db)):
    """
    Manually set the system SF 311 token.
    Use this to initialize the token with working credentials.
    """
    try:
        # Check if system token already exists
        existing = db.query(SystemConfig).filter(
            SystemConfig.key == "sf311_system_token"
        ).first()
        
        token_dict = {
            "access_token": token_data.access_token,
            "refresh_token": token_data.refresh_token,
            "expires_in": token_data.expires_in,
            "obtained_at": token_data.obtained_at,
        }
        
        if existing:
            existing.value = json.dumps(token_dict)
            existing.last_updated_timestamp = token_data.obtained_at
            message = "System token updated"
        else:
            config = SystemConfig(
                key="sf311_system_token",
                value=json.dumps(token_dict),
                last_updated_timestamp=token_data.obtained_at,
            )
            db.add(config)
            message = "System token created"
        
        db.commit()
        
        return {
            "status": "success",
            "message": message,
            "expires_at": token_data.obtained_at + token_data.expires_in,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error setting token: {str(e)}")
