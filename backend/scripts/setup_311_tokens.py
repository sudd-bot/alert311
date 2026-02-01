#!/usr/bin/env python3
"""
Helper script to set up 311 API tokens.
Uses the reporter auth flow to get tokens, then stores them.
"""
import sys
from pathlib import Path

# Add parent and reporter directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "reporter"))

import asyncio
from app.services.sf311 import sf311_client
from app.core.config import settings

# Import from reporter
import auth


async def main():
    print("Setting up SF 311 API tokens...")
    print(f"Base URL: {settings.SF311_BASE_URL}")
    print(f"Client ID: {settings.SF311_CLIENT_ID}")
    print()
    
    # Run OAuth flow (requires browser interaction)
    print("Starting OAuth flow (this will open a browser)...")
    
    user_agent_web = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    user_agent_app = "Reporters/5291 CFNetwork/3826.500.131 Darwin/24.5.0"
    
    try:
        tokens = auth.acquire_tokens(
            base_url=settings.SF311_BASE_URL,
            client_id=settings.SF311_CLIENT_ID,
            redirect_uri=settings.SF311_REDIRECT_URI,
            scope=settings.SF311_SCOPE,
            identity_provider_id=None,
            user_agent_web=user_agent_web,
            user_agent_app=user_agent_app,
            timeout=30,
        )
        
        print("\n✅ Tokens acquired successfully!")
        print(f"Access token: {tokens.access_token[:20]}...")
        print(f"Refresh token: {tokens.refresh_token[:20]}...")
        print(f"Expires in: {tokens.expires_in} seconds")
        
        # Set tokens in the client
        sf311_client.set_tokens(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )
        
        # Test the tokens by making a simple query
        print("\nTesting tokens with a sample query...")
        reports = await sf311_client.search_reports(
            latitude=37.7749,
            longitude=-122.4194,
            limit=5,
        )
        
        print(f"✅ Token test successful! Found {len(reports)} reports.")
        
        print("\n⚠️  TODO: Store these tokens in your database or environment!")
        print("For now, they're only in memory and will be lost when this script exits.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
