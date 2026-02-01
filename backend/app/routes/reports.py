"""
Report viewing routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..models import User, Report, Alert
from ..schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=List[ReportResponse])
async def list_user_reports(phone: str, db: Session = Depends(get_db)):
    """
    List all reports for all of a user's alerts.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all alert IDs for this user
    alert_ids = [alert.id for alert in user.alerts]
    
    if not alert_ids:
        return []
    
    # Get all reports for these alerts
    reports = db.query(Report).filter(Report.alert_id.in_(alert_ids)).order_by(
        Report.created_at.desc()
    ).all()
    
    return reports


@router.get("/{alert_id}", response_model=List[ReportResponse])
async def list_alert_reports(alert_id: int, phone: str, db: Session = Depends(get_db)):
    """
    List all reports for a specific alert.
    """
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify alert belongs to user
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    reports = db.query(Report).filter(Report.alert_id == alert_id).order_by(
        Report.created_at.desc()
    ).all()
    
    return reports
