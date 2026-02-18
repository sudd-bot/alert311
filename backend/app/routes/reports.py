"""
Report viewing routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from pydantic import BaseModel
import json
import math
import urllib.request
import urllib.error
import ssl
import asyncio
from datetime import datetime

from ..core.database import get_db
from ..models import User, Report, Alert
from ..schemas import ReportResponse
from ..services.token_manager import TokenManager

router = APIRouter(prefix="/reports", tags=["reports"])


def _normalize_addr(a: str) -> str:
    """
    Normalize street-type abbreviations for address fuzzy matching.
    Covers 13 common street types, applied symmetrically to both query and ticket address.
    Defined at module level so it's compiled once at import time (not per-request).
    """
    a = a.lower().strip()
    # Remove punctuation
    a = a.replace(".", "").replace(",", "")
    # Full → abbreviated (longer strings first to avoid partial matches)
    replacements = [
        (" boulevard", " blvd"),
        (" terrace", " ter"),
        (" avenue", " ave"),
        (" street", " st"),
        (" drive", " dr"),
        (" court", " ct"),
        (" place", " pl"),
        (" lane", " ln"),
        (" road", " rd"),
        (" circle", " cir"),
        (" highway", " hwy"),
        (" parkway", " pkwy"),
        (" square", " sq"),
    ]
    for full, abbr in replacements:
        a = a.replace(full, abbr)
    return a


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance between two points in meters (Haversine formula)."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class SF311Report(BaseModel):
    id: str
    public_id: Optional[str] = None
    type: str
    date: str
    raw_date: Optional[str] = None  # ISO 8601 string for accurate client-side relative-time formatting
    status: str
    address: str
    latitude: float
    longitude: float
    photo_url: Optional[str] = None
    distance_meters: Optional[float] = None  # Great-circle distance from the query point


@router.get("/nearby", response_model=List[SF311Report])
async def get_nearby_reports(
    lat: float,
    lng: float,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
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
        
        # If filtering by address, fetch more tickets to ensure we get enough matches
        fetch_limit = 50 if address else limit

        GRAPHQL_QUERY = """query ExploreQuery($scope: TicketsScopeEnum, $order: Json, $filters: Json, $limit: Int) {
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

        def fetch_scope(scope: str) -> list:
            """Fetch tickets for a single scope (blocking I/O, runs in thread pool)."""
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
                "query": GRAPHQL_QUERY,
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method="POST")
            for k, v in headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=10, context=context) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result.get("data", {}).get("tickets", {}).get("nodes", [])

        # Fetch recently_opened and recently_closed in parallel (cuts latency ~50%)
        opened_tickets, closed_tickets = await asyncio.gather(
            asyncio.to_thread(fetch_scope, "recently_opened"),
            asyncio.to_thread(fetch_scope, "recently_closed"),
        )
        raw_tickets = opened_tickets + closed_tickets
        
        # Deduplicate by ticket ID (same ticket can appear in both recently_opened and recently_closed)
        seen_ids: set = set()
        all_tickets = []
        for ticket in raw_tickets:
            ticket_id = ticket.get("id")
            if ticket_id and ticket_id not in seen_ids:
                seen_ids.add(ticket_id)
                all_tickets.append(ticket)
        
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
                except (ValueError, TypeError, AttributeError):
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
            
            # Get photo URL if available — strip Cloudinary #spot=... fragment (frontend-safe, cleaner URLs)
            photos = ticket.get("photos", [])
            raw_photo_url = photos[0]["url"] if photos else None
            photo_url = raw_photo_url.split("#")[0] if raw_photo_url else None
            
            location = ticket.get("location", {})
            ticket_lat = location.get("latitude", lat)
            ticket_lng = location.get("longitude", lng)
            distance_m = _haversine_meters(lat, lng, ticket_lat, ticket_lng)
            
            reports.append({
                "report": SF311Report(
                    id=ticket["id"],
                    public_id=ticket.get("publicId"),
                    type=ticket.get("ticketType", {}).get("name", "Unknown"),
                    date=date,
                    raw_date=date_str or None,  # ISO 8601 string for client-side relative-time formatting
                    status=status,
                    address=location.get("address", "Unknown"),
                    latitude=ticket_lat,
                    longitude=ticket_lng,
                    photo_url=photo_url,
                    distance_meters=round(distance_m, 1)
                ),
                "date_obj": date_obj  # Keep datetime object for sorting
            })
        
        # Filter by address if provided
        if address:
            # Normalize the target address
            target_addr = _normalize_addr(address)
            
            # Filter to only include tickets that match the address
            filtered_reports = []
            for r in reports:
                ticket_addr = _normalize_addr(r["report"].address)
                
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
        
        # Sort by distance (closest first) — most spatially relevant for map exploration.
        # Ties (same distance) break on recency (newest first) so fresh reports surface naturally.
        reports.sort(key=lambda x: (
            x["report"].distance_meters if x["report"].distance_meters is not None else float('inf'),
            -(x["date_obj"].timestamp() if x["date_obj"] else 0),
        ))
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
