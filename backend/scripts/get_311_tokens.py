#!/usr/bin/env python3
"""
Helper script for users to get their SF 311 OAuth tokens.
Uses the reporter auth flow.

Usage:
    python scripts/get_311_tokens.py

This will:
1. Run the OAuth flow (opens browser)
2. Print the tokens
3. Show you how to save them via API
"""
import sys
from pathlib import Path

# Add parent directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from reporter_lib import auth


def main():
    print("=" * 60)
    print("SF 311 OAuth Token Generator")
    print("=" * 60)
    print()
    print("This will open a browser for you to sign in to SF 311.")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    base_url = "https://mobile311.sfgov.org"
    client_id = "KLHhIUu56qWPHrYA16MUvxBXaJbPoAmKDbFjDFhe"
    redirect_uri = "sf311://auth"
    scope = "refresh_token read write openid"
    
    user_agent_web = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    user_agent_app = "Reporters/5291 CFNetwork/3826.500.131 Darwin/24.5.0"
    
    try:
        print("\n🔐 Starting OAuth flow...\n")
        
        tokens = auth.acquire_tokens(
            base_url=base_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            identity_provider_id=None,
            user_agent_web=user_agent_web,
            user_agent_app=user_agent_app,
            timeout=60,
        )
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Here are your tokens:")
        print("=" * 60)
        print()
        print(f"access_token: {tokens.access_token}")
        print(f"refresh_token: {tokens.refresh_token}")
        print(f"expires_in: {tokens.expires_in}")
        print()
        print("=" * 60)
        print("To save these tokens to your account:")
        print("=" * 60)
        print()
        print("curl -X POST 'https://your-api.vercel.app/sf311/save-tokens?phone=+1234567890' \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print(f'    "access_token": "{tokens.access_token}",')
        print(f'    "refresh_token": "{tokens.refresh_token}",')
        print(f'    "expires_in": {tokens.expires_in}')
        print("  }'")
        print()
        print("(Replace the URL and phone number with yours)")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
