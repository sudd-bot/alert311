"""
SF 311 OAuth routes for users to authenticate with the 311 API.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..models import User
from ..schemas import SuccessResponse
from ..services.sf311 import sf311_client

router = APIRouter(prefix="/sf311", tags=["sf311-auth"])


class TokensInput(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600


@router.post("/save-tokens", response_model=SuccessResponse)
async def save_311_tokens(
    phone: str,
    tokens: TokensInput,
    db: Session = Depends(get_db)
):
    """
    Save 311 OAuth tokens for a user.
    
    User must complete the OAuth flow externally (e.g., via the reporter script)
    and then submit the tokens here.
    
    TODO: Implement full OAuth flow in the app itself.
    """
    # Get user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.verified:
        raise HTTPException(status_code=403, detail="Phone number not verified")
    
    # Save tokens
    sf311_client.save_tokens_to_user(
        user=user,
        db=db,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
    
    return SuccessResponse(
        success=True,
        message="311 tokens saved successfully"
    )


@router.get("/token-status", response_model=dict)
async def check_311_token_status(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Check if user has valid 311 tokens.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    has_tokens = bool(user.sf311_access_token and user.sf311_refresh_token)
    
    return {
        "has_tokens": has_tokens,
        "token_expires_at": user.sf311_token_expires_at if has_tokens else None,
    }
