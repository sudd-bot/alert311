#!/usr/bin/env python3
"""
Test script to verify services are configured correctly.
"""
import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.geocoding import geocoding_service


async def test_geocoding():
    """Test geocoding service."""
    print("Testing geocoding service...")
    test_address = "1 Market St, San Francisco, CA"
    
    coords = geocoding_service.geocode(test_address)
    if coords:
        lat, lon = coords
        print(f"✅ Geocoding works! {test_address} -> ({lat}, {lon})")
        return True
    else:
        print(f"❌ Geocoding failed for {test_address}")
        return False


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    required_vars = [
        "DATABASE_URL",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_VERIFY_SERVICE_SID",
        "CRON_SECRET",
    ]
    
    missing = []
    for var in required_vars:
        value = getattr(settings, var, None)
        if not value or value == "":
            missing.append(var)
        else:
            print(f"  ✅ {var}: {value[:10]}...")
    
    if missing:
        print(f"\n❌ Missing required variables: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All required config variables set!")
        return True


async def main():
    """Run all tests."""
    print("=== Alert311 Service Tests ===\n")
    
    config_ok = test_config()
    geocoding_ok = await test_geocoding()
    
    print("\n=== Summary ===")
    print(f"Config: {'✅ OK' if config_ok else '❌ FAIL'}")
    print(f"Geocoding: {'✅ OK' if geocoding_ok else '❌ FAIL'}")
    
    if config_ok and geocoding_ok:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
