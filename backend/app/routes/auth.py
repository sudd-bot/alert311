"""
Authentication routes for user registration and phone verification.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import User
from ..schemas import UserRegister, UserVerify, UserResponse, SuccessResponse
from ..services.twilio_verify import twilio_verify_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=SuccessResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user with phone number.
    Sends SMS verification code.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.phone == user_data.phone).first()
    if existing_user:
        if existing_user.verified:
            raise HTTPException(status_code=400, detail="Phone number already registered and verified")
        # User exists but not verified, resend verification
        user = existing_user
    else:
        # Create new user
        user = User(phone=user_data.phone, verified=False)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Send verification code
    success = twilio_verify_service.send_verification(user_data.phone)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification code")
    
    return SuccessResponse(
        success=True,
        message="Verification code sent to phone number"
    )


@router.post("/verify", response_model=UserResponse)
async def verify_phone(verify_data: UserVerify, db: Session = Depends(get_db)):
    """
    Verify phone number with code sent via SMS.
    """
    # Get user
    user = db.query(User).filter(User.phone == verify_data.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.verified:
        # Already verified, just return user data
        return user
    
    # Check verification code
    success = twilio_verify_service.check_verification(verify_data.phone, verify_data.code)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Mark user as verified
    user.verified = True
    db.commit()
    db.refresh(user)
    
    # Auto-assign SF 311 token to user
    try:
        from ..services.token_manager import TokenManager
        await TokenManager.assign_token_to_user(user, db)
    except Exception as e:
        # Log but don't fail - token can be assigned later
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to assign SF 311 token to user {user.phone}: {e}")
    
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user(phone: str, db: Session = Depends(get_db)):
    """
    Get current user by phone number.
    TODO: Replace with proper JWT authentication.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user
