"""
Report viewing routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime

from ..core.database import get_db
from ..models import User, Report, Alert
from ..schemas import ReportResponse
from ..services.token_manager import TokenManager

router = APIRouter(prefix="/reports", tags=["reports"])


class SF311Report(BaseModel):
    id: str
    type: str
    date: str
    status: str
    address: str
    latitude: float
    longitude: float
    photo_url: Optional[str] = None


@router.get("/nearby", response_model=List[SF311Report])
async def get_nearby_reports(
    lat: float,
    lng: float,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Fetch recent 311 reports near a location using SF 311 API.
    """
    try:
        # Ensure system token exists (auto-initialize if missing)
        await TokenManager.ensure_system_token_exists(db)
        
        # Get system token
        token = await TokenManager.get_system_token(db)
        if not token:
            raise HTTPException(status_code=500, detail="No SF 311 token available")
        
        # Build GraphQL query
        payload = {
            "operationName": "ExploreQuery",
            "variables": {
                "scope": "recently_opened",
                "order": {
                    "by": "distance",
                    "direction": "ascending",
                    "latitude": lat,
                    "longitude": lng,
                },
                "filters": {
                    "ticket_type_id": ["963f1454-7c22-43be-aacb-3f34ae5d0dc7"],  # Parking violations
                },
                "limit": limit,
            },
            "query": """query ExploreQuery($scope: TicketsScopeEnum, $order: Json, $filters: Json, $limit: Int) {
                tickets(first: $limit, scope: $scope, order: $order, filters: $filters) {
                    nodes {
                        id
                        publicId
                        status
                        statusLabel
                        submittedAt
                        openedAt
                        closedAt
                        ticketType {
                            name
                        }
                        location {
                            address
                            latitude
                            longitude
                        }
                        photos {
                            url
                        }
                    }
                }
            }"""
        }
        
        # Make API request
        url = "https://san-francisco2-production.spotmobile.net/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)
        
        context = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # Parse response
        reports = []
        tickets = result.get("data", {}).get("tickets", {}).get("nodes", [])
        
        for ticket in tickets:
            # Determine date to display
            date_str = ticket.get("openedAt") or ticket.get("submittedAt") or ""
            date_obj = None
            if date_str:
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date = date_obj.strftime("%b %d, %Y")
                except:
                    date = date_str
            else:
                date = "Unknown"
            
            # Get photo URL if available
            photos = ticket.get("photos", [])
            photo_url = photos[0]["url"] if photos else None
            
            location = ticket.get("location", {})
            
            reports.append({
                "report": SF311Report(
                    id=ticket["id"],
                    type=ticket.get("ticketType", {}).get("name", "Unknown"),
                    date=date,
                    status=ticket.get("status", "unknown"),
                    address=location.get("address", "Unknown"),
                    latitude=location.get("latitude", lat),
                    longitude=location.get("longitude", lng),
                    photo_url=photo_url
                ),
                "date_obj": date_obj  # Keep datetime object for sorting
            })
        
        # Sort by date (newest first), then return just the reports
        reports.sort(key=lambda x: x["date_obj"] if x["date_obj"] else datetime.min, reverse=True)
        return [r["report"] for r in reports]
        
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"SF 311 API error: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")


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
