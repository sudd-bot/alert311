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
    address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Fetch recent 311 reports near a location using SF 311 API.
    Combines both recently opened and recently closed tickets.
    If address is provided, filters to only show tickets at or very near that address.
    """
    try:
        # Ensure system token exists (auto-initialize if missing)
        await TokenManager.ensure_system_token_exists(db)
        
        # Get system token
        token = await TokenManager.get_system_token(db)
        if not token:
            raise HTTPException(status_code=500, detail="No SF 311 token available")
        
        # Prepare API request setup
        url = "https://san-francisco2-production.spotmobile.net/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        context = ssl.create_default_context()
        
        all_tickets = []
        
        # If filtering by address, fetch more tickets to ensure we get enough matches
        fetch_limit = 50 if address else limit
        
        # Fetch both recently_opened and recently_closed tickets
        for scope in ["recently_opened", "recently_closed"]:
            payload = {
                "operationName": "ExploreQuery",
                "variables": {
                    "scope": scope,
                    "order": {
                        "by": "distance",
                        "direction": "ascending",
                        "latitude": lat,
                        "longitude": lng,
                    },
                    "filters": {
                        "ticket_type_id": ["963f1454-7c22-43be-aacb-3f34ae5d0dc7"],  # Parking violations
                    },
                    "limit": fetch_limit,
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
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method="POST")
            for k, v in headers.items():
                req.add_header(k, v)
            
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                result = json.loads(response.read().decode('utf-8'))
                tickets = result.get("data", {}).get("tickets", {}).get("nodes", [])
                all_tickets.extend(tickets)
        
        # Parse all tickets (from both scopes)
        reports = []
        
        for ticket in all_tickets:
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
            
            # Determine status - normalize to "open" or "closed"
            # Check both status field and closedAt field
            ticket_status = ticket.get("status", "unknown").lower()
            closed_at = ticket.get("closedAt")
            
            # If there's a closedAt date, treat as closed regardless of status field
            if closed_at:
                status = "closed"
            elif ticket_status in ["closed", "resolved", "completed"]:
                status = "closed"
            elif ticket_status in ["open", "submitted", "acknowledged"]:
                status = "open"
            else:
                status = ticket_status
            
            # Get photo URL if available
            photos = ticket.get("photos", [])
            photo_url = photos[0]["url"] if photos else None
            
            location = ticket.get("location", {})
            
            reports.append({
                "report": SF311Report(
                    id=ticket["id"],
                    type=ticket.get("ticketType", {}).get("name", "Unknown"),
                    date=date,
                    status=status,
                    address=location.get("address", "Unknown"),
                    latitude=location.get("latitude", lat),
                    longitude=location.get("longitude", lng),
                    photo_url=photo_url
                ),
                "date_obj": date_obj  # Keep datetime object for sorting
            })
        
        # Filter by address if provided
        if address:
            # Normalize the target address
            target_addr = address.lower().replace(" street", " st").replace(" avenue", " ave").replace(".", "")
            
            # Filter to only include tickets that match the address
            filtered_reports = []
            for r in reports:
                ticket_addr = r["report"].address.lower().replace(" street", " st").replace(" avenue", " ave").replace(".", "")
                
                # Extract street number and name for comparison
                # E.g., "61 Chattanooga St" -> "61 chattanooga st"
                if target_addr in ticket_addr or ticket_addr in target_addr:
                    filtered_reports.append(r)
                # Also try matching just the street number
                elif address.split()[0].isdigit():
                    target_number = address.split()[0]
                    if ticket_addr.startswith(target_number + " "):
                        # Same street number - check if street name matches
                        target_street = " ".join(target_addr.split()[1:])
                        ticket_street = " ".join(ticket_addr.split()[1:])
                        if target_street in ticket_street or ticket_street in target_street:
                            filtered_reports.append(r)
            
            reports = filtered_reports
        
        # Sort by date (newest first), then limit to requested amount
        reports.sort(key=lambda x: x["date_obj"] if x["date_obj"] else datetime.min, reverse=True)
        return [r["report"] for r in reports[:limit]]
        
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
