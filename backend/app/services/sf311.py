"""
SF 311 API client using OAuth + GraphQL.
Adapted from reporter/get_reports.py and reporter/auth.py
"""
from __future__ import annotations

import time
import json
import httpx
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Add reporter_lib directory to path for reporter code
lib_path = Path(__file__).parent.parent.parent / "reporter_lib"
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))

from ..core.config import settings


@dataclass
class SF311Tokens:
    access_token: str
    refresh_token: str
    expires_in: int
    obtained_at: int


class SF311Client:
    """Client for SF 311 API (Spotmobile GraphQL)."""
    
    def __init__(self):
        self.base_url = settings.SF311_BASE_URL
        self.client_id = settings.SF311_CLIENT_ID
        self.redirect_uri = settings.SF311_REDIRECT_URI
        self.scope = settings.SF311_SCOPE
        self.graphql_url = settings.SF311_GRAPHQL_URL
    
    async def _acquire_tokens(self) -> SF311Tokens:
        """
        Run full OAuth flow to get initial tokens.
        This requires browser interaction, so for now we'll use cached tokens.
        In production, implement proper OAuth flow.
        """
        # TODO: Implement full OAuth flow
        # For now, assume tokens are loaded from environment or database
        raise NotImplementedError("OAuth flow not yet implemented - use cached tokens")
    
    async def _refresh_tokens(self, refresh_token: str) -> SF311Tokens:
        """Refresh access token using refresh_token."""
        try:
            import auth
            
            # Use the auth module's refresh function (it's synchronous)
            tokens = auth.refresh_tokens(
                base_url=self.base_url,
                client_id=self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scope,
                refresh_token=refresh_token,
                user_agent_app="Alert311/1.0",
                timeout=30,
            )
            
            return SF311Tokens(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_in=tokens.expires_in,
                obtained_at=int(time.time()),
            )
        except Exception as e:
            # Fallback to manual refresh if auth module fails
            url = f"{self.base_url}/oauth/token"
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": refresh_token,
                "redirect_uri": self.redirect_uri,
                "scope": self.scope,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=30.0)
                response.raise_for_status()
                
                token_data = response.json()
                return SF311Tokens(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token", refresh_token),
                    expires_in=token_data.get("expires_in", 3600),
                    obtained_at=int(time.time()),
                )
    
    async def _get_valid_token_for_user(self, user, db) -> str:
        """
        Get a valid access token for a user, refreshing if necessary.
        Updates the user's tokens in the database if refreshed.
        
        Args:
            user: User model instance
            db: Database session
        
        Returns:
            Valid access token
        """
        if not user.sf311_access_token or not user.sf311_refresh_token:
            raise RuntimeError("User has no 311 tokens. Need to complete OAuth flow.")
        
        # Check if token is expired (with 5 min buffer)
        now = int(time.time())
        
        if user.sf311_token_expires_at and now >= (user.sf311_token_expires_at - 300):
            # Token expired or about to expire, refresh it
            new_tokens = await self._refresh_tokens(user.sf311_refresh_token)
            
            # Update user's tokens in database
            user.sf311_access_token = new_tokens.access_token
            user.sf311_refresh_token = new_tokens.refresh_token
            user.sf311_token_expires_at = new_tokens.obtained_at + new_tokens.expires_in
            db.commit()
            
            return new_tokens.access_token
        
        return user.sf311_access_token
    
    async def search_reports(
        self,
        latitude: float,
        longitude: float,
        ticket_type_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        scope: str = "recently_opened",
        access_token: Optional[str] = None,
        user=None,
        db=None,
    ) -> List[Dict[str, Any]]:
        """
        Search for 311 reports near a location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            ticket_type_id: Filter by specific ticket type (e.g., parking on sidewalk)
            search: Text search filter
            limit: Max number of results
            scope: "recently_opened" or "recently_closed"
            access_token: Optional raw access token. If provided, user/db are not required.
            user: Optional User model instance (with 311 tokens). Required if access_token not provided.
            db: Optional Database session. Required if access_token not provided.

        Returns:
            List of report dictionaries
        """
        if access_token:
            # Use the provided token directly
            token = access_token
        else:
            # Get token from user (legacy behavior for backwards compatibility)
            if not user or not db:
                raise ValueError("Must provide either access_token OR both user and db")
            token = await self._get_valid_token_for_user(user, db)
        
        # Build GraphQL payload (from reporter/spotclient/graphql.py logic)
        payload = self._build_search_payload(
            latitude=latitude,
            longitude=longitude,
            ticket_type_id=ticket_type_id,
            search=search,
            limit=limit,
            scope=scope,
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Alert311/1.0",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.graphql_url,
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract tickets from GraphQL response
            return self._extract_tickets(data)
    
    def _build_search_payload(
        self,
        latitude: float,
        longitude: float,
        ticket_type_id: Optional[str],
        search: Optional[str],
        limit: int,
        scope: str,
    ) -> Dict[str, Any]:
        """Build GraphQL query payload."""
        variables: Dict[str, Any] = {
            "scope": scope,
            "limit": limit,
            "order": {
                "latitude": latitude,
                "longitude": longitude,
            },
            "filters": {},
        }
        
        if ticket_type_id:
            variables["filters"]["ticket_type_id"] = ticket_type_id
        if search:
            variables["filters"]["search"] = search
        
        # GraphQL query (simplified from reporter code)
        query = """
        query ExploreQuery($scope: Scope!, $limit: Int, $order: OrderInput, $filters: FiltersInput) {
          explore(scope: $scope, limit: $limit, order: $order, filters: $filters) {
            id
            description
            address
            latitude
            longitude
            status
            ticket_type_id
            ticket_type_name
            created_at
            updated_at
            closed_at
          }
        }
        """
        
        return {
            "operationName": "ExploreQuery",
            "query": query,
            "variables": variables,
        }
    
    def _extract_tickets(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract ticket list from GraphQL response."""
        if "data" not in response_data:
            return []
        
        explore_data = response_data["data"].get("explore")
        if not explore_data:
            return []
        
        return explore_data if isinstance(explore_data, list) else []
    
    def save_tokens_to_user(self, user, db, access_token: str, refresh_token: str, expires_in: int = 3600):
        """
        Save 311 OAuth tokens to a user in the database.
        
        Args:
            user: User model instance
            db: Database session
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiration time in seconds
        """
        user.sf311_access_token = access_token
        user.sf311_refresh_token = refresh_token
        user.sf311_token_expires_at = int(time.time()) + expires_in
        db.commit()


sf311_client = SF311Client()
