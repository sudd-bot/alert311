"""
Cron job endpoints for Vercel Cron.
These endpoints should be called by Vercel Cron on a schedule.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.config import settings
from ..models import Alert, Report
from ..schemas import SuccessResponse
from ..services.sf311 import sf311_client
from ..services.sms_alert import sms_alert_service
from ..services.address_utils import addresses_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["cron"])


def verify_cron_secret(authorization: Optional[str] = Header(None)):
    """Verify cron job secret token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if authorization != f"Bearer {settings.CRON_SECRET}":
        raise HTTPException(status_code=403, detail="Invalid cron secret")


@router.post("/poll-reports", response_model=SuccessResponse)
async def poll_311_reports(
    db: Session = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """
    Poll 311 API for new reports matching active alerts.
    Run this every 5 minutes via Vercel Cron.
    """
    # Get all active alerts
    active_alerts = db.query(Alert).filter(Alert.active == True).all()
    
    if not active_alerts:
        return SuccessResponse(
            success=True,
            message="No active alerts to check"
        )
    
    new_reports_count = 0
    
    # Get system token for API calls (fallback if user doesn't have tokens)
    from ..services.token_manager import TokenManager
    system_token = await TokenManager.get_system_token(db)
    
    for alert in active_alerts:
        try:
            # Get the user for this alert
            user = alert.user
            
            # Try to get user-specific token, fall back to system token
            try:
                access_token = await TokenManager.get_user_token(user, db)
            except RuntimeError:
                # User doesn't have tokens yet, use system token
                access_token = system_token
            
            # Search for reports near this alert's location using raw token
            reports = await sf311_client.search_reports(
                latitude=alert.latitude,
                longitude=alert.longitude,
                ticket_type_id=alert.report_type_id,
                limit=20,
                scope="recently_opened",
                access_token=access_token,
            )
            
            # Filter reports to address match.
            # Uses fuzzy normalization (abbreviations + substring) so that
            # "580 California St" matches "580 California St, San Francisco, CA"
            # and "61 Chattanooga Street" matches "61 Chattanooga St".
            # Previously used exact case-insensitive match which would NEVER fire
            # because geocoded alert addresses include city/state suffix that SF311 omits.
            for report_data in reports:
                report_address = report_data.get("address", "").strip()
                
                if not addresses_match(report_address, alert.address):
                    continue
                
                report_id = report_data.get("id")
                if not report_id:
                    continue
                
                # Check if we've already stored this report
                existing_report = db.query(Report).filter(
                    Report.report_id == report_id
                ).first()
                
                if existing_report:
                    continue
                
                # Store new report
                new_report = Report(
                    alert_id=alert.id,
                    report_id=report_id,
                    report_data=report_data,
                    sms_sent=False,
                )
                db.add(new_report)
                new_reports_count += 1
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error polling reports for alert {alert.id}: {e}")
            continue
    
    return SuccessResponse(
        success=True,
        message=f"Polled reports. Found {new_reports_count} new matches."
    )


@router.post("/send-alerts", response_model=SuccessResponse)
async def send_pending_alerts(
    db: Session = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """
    Send SMS alerts for reports that haven't been sent yet.
    Run this every 5 minutes via Vercel Cron.
    """
    # Get all reports that need SMS sent
    pending_reports = db.query(Report).filter(Report.sms_sent == False).all()
    
    if not pending_reports:
        return SuccessResponse(
            success=True,
            message="No pending alerts to send"
        )
    
    sent_count = 0
    
    for report in pending_reports:
        try:
            # Get the alert and user info
            alert = report.alert
            if not alert or not alert.active:
                # Alert was deleted or deactivated, skip
                report.sms_sent = True  # Mark as sent to avoid retrying
                continue
            
            user = alert.user
            if not user or not user.verified:
                # User not verified, skip
                continue
            
            # Send SMS alert
            success = sms_alert_service.send_alert(
                to_phone=user.phone,
                report_data=report.report_data
            )
            
            if success:
                report.sms_sent = True
                sent_count += 1
            
        except Exception as e:
            logger.error(f"Error sending alert for report {report.id}: {e}")
            continue
    
    db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Sent {sent_count} SMS alerts"
    )


@router.post("/refresh-tokens", response_model=dict)
async def refresh_sf311_tokens(
    db: Session = Depends(get_db),
    _: None = Depends(verify_cron_secret)
):
    """
    Proactively refresh SF 311 tokens (system + users).
    Run this every 12 hours via Vercel Cron.
    
    Returns counts of refreshed tokens.
    """
    from ..services.token_manager import TokenManager
    
    try:
        # Refresh system token
        await TokenManager.refresh_system_token_proactively(db)
        
        # Refresh user tokens expiring within 24 hours
        user_results = await TokenManager.refresh_user_tokens_proactively(db)
        
        return {
            "success": True,
            "message": "Token refresh complete",
            "system_token": "refreshed",
            "user_tokens": user_results,
        }
        
    except Exception as e:
        logger.error(f"Error in token refresh cron: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Token refresh failed: {str(e)}"
        )
