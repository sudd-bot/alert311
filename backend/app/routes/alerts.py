"""
Alert management routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..core.config import settings
from ..models import User, Alert
from ..schemas import AlertCreate, AlertUpdate, AlertResponse, SuccessResponse
from ..services.geocoding import geocoding_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse)
async def create_alert(
    phone: str,
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new alert for a user.
    Requires verified phone number.
    """
    # Get user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.verified:
        raise HTTPException(status_code=403, detail="Phone number not verified")
    
    # Geocode the address
    coords = geocoding_service.geocode(alert_data.address)
    if not coords:
        raise HTTPException(status_code=400, detail="Unable to geocode address")
    
    latitude, longitude = coords
    
    # Use default report type if not specified
    report_type_id = alert_data.report_type_id or settings.DEFAULT_REPORT_TYPE_ID
    report_type_name = settings.DEFAULT_REPORT_TYPE_NAME  # TODO: Look up from config
    
    # Create alert
    alert = Alert(
        user_id=user.id,
        address=alert_data.address,
        latitude=latitude,
        longitude=longitude,
        report_type_id=report_type_id,
        report_type_name=report_type_name,
        active=True,
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert


@router.get("", response_model=List[AlertResponse])
async def list_alerts(phone: str, db: Session = Depends(get_db)):
    """
    List all alerts for a user.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alerts = db.query(Alert).filter(Alert.user_id == user.id).all()
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, phone: str, db: Session = Depends(get_db)):
    """
    Get a specific alert.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    phone: str,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an alert (e.g., activate/deactivate).
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.active = alert_update.active
    db.commit()
    db.refresh(alert)
    
    return alert


@router.delete("/{alert_id}", response_model=SuccessResponse)
async def delete_alert(alert_id: int, phone: str, db: Session = Depends(get_db)):
    """
    Delete an alert.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return SuccessResponse(success=True, message="Alert deleted")
