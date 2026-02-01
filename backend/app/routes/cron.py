"""
Cron job endpoints for Vercel Cron.
These endpoints should be called by Vercel Cron on a schedule.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional

from ..core.database import get_db
from ..core.config import settings
from ..models import Alert, Report
from ..schemas import SuccessResponse
from ..services.sf311 import sf311_client
from ..services.sms_alert import sms_alert_service

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
    
    for alert in active_alerts:
        try:
            # Get the user for this alert (to access their 311 tokens)
            user = alert.user
            
            if not user.sf311_access_token:
                # User hasn't completed 311 OAuth yet, skip
                continue
            
            # Search for reports near this alert's location
            reports = await sf311_client.search_reports(
                user=user,
                db=db,
                latitude=alert.latitude,
                longitude=alert.longitude,
                ticket_type_id=alert.report_type_id,
                limit=20,
                scope="recently_opened",
            )
            
            # Filter reports to exact address match
            for report_data in reports:
                report_address = report_data.get("address", "").strip()
                
                # Exact address match (case-insensitive)
                if report_address.lower() != alert.address.lower():
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
            print(f"Error polling reports for alert {alert.id}: {e}")
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
            print(f"Error sending alert for report {report.id}: {e}")
            continue
    
    db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Sent {sent_count} SMS alerts"
    )
