"""
Admin routes for manual operations and stats.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import json

from ..core.database import get_db
from ..models import SystemConfig, User, Alert, Report

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


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get system statistics.
    Returns aggregate data about users, alerts, and reports.
    """
    try:
        # User stats
        total_users = db.query(func.count(User.id)).scalar()
        verified_users = db.query(func.count(User.id)).filter(User.verified == True).scalar()

        # Alert stats
        total_alerts = db.query(func.count(Alert.id)).scalar()
        active_alerts = db.query(func.count(Alert.id)).filter(Alert.active == True).scalar()

        # Report stats (stored reports in database)
        total_reports = db.query(func.count(Report.id)).scalar()

        # Alert activity (alerts per user)
        avg_alerts_per_user = 0
        if total_users > 0:
            avg_alerts_per_user = round(total_alerts / total_users, 2)

        # Active alert rate
        active_alert_rate = 0
        if total_alerts > 0:
            active_alert_rate = round((active_alerts / total_alerts) * 100, 1)

        return {
            "users": {
                "total": total_users,
                "verified": verified_users,
                "unverified": total_users - verified_users,
                "verified_rate": round((verified_users / total_users * 100), 1) if total_users > 0 else 0,
            },
            "alerts": {
                "total": total_alerts,
                "active": active_alerts,
                "inactive": total_alerts - active_alerts,
                "avg_per_user": avg_alerts_per_user,
                "active_rate": active_alert_rate,
            },
            "reports": {
                "total_stored": total_reports,
            },
        }

    except Exception as e:
        # Return error but with available stats if partial data is retrieved
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
