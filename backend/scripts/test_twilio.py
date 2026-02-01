#!/usr/bin/env python3
"""
Test Twilio setup - verify credentials and send test messages.

Usage:
    python scripts/test_twilio.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def test_credentials():
    """Check if Twilio credentials are configured."""
    print("🔍 Checking Twilio credentials...\n")
    
    required = {
        "TWILIO_ACCOUNT_SID": settings.TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": settings.TWILIO_AUTH_TOKEN,
        "TWILIO_VERIFY_SERVICE_SID": settings.TWILIO_VERIFY_SERVICE_SID,
    }
    
    optional = {
        "TWILIO_FROM_NUMBER": settings.TWILIO_FROM_NUMBER,
    }
    
    all_ok = True
    
    for key, value in required.items():
        if value and value != "":
            print(f"  ✅ {key}: {value[:10]}...")
        else:
            print(f"  ❌ {key}: MISSING")
            all_ok = False
    
    for key, value in optional.items():
        if value and value != "":
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ⚠️  {key}: Not set (needed for SMS alerts)")
    
    print()
    return all_ok


def test_verify_service():
    """Test Twilio Verify service."""
    print("📱 Testing Verify service...\n")
    
    try:
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Try to get the verify service
        service = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).fetch()
        
        print(f"  ✅ Verify service found!")
        print(f"     Name: {service.friendly_name}")
        print(f"     SID: {service.sid}")
        print()
        
        # Ask if they want to test sending a verification code
        test_phone = input("  Enter phone number to test verification (or press Enter to skip): ").strip()
        
        if test_phone:
            if not test_phone.startswith("+"):
                print("  ⚠️  Phone should start with + (e.g., +16464171584)")
                return True
            
            print(f"  📤 Sending verification code to {test_phone}...")
            
            verification = client.verify.v2.services(
                settings.TWILIO_VERIFY_SERVICE_SID
            ).verifications.create(to=test_phone, channel="sms")
            
            if verification.status == "pending":
                print(f"  ✅ Verification code sent! Status: {verification.status}")
                print()
                
                # Ask for code to verify
                code = input("  Enter the code you received (or press Enter to skip): ").strip()
                
                if code:
                    check = client.verify.v2.services(
                        settings.TWILIO_VERIFY_SERVICE_SID
                    ).verification_checks.create(to=test_phone, code=code)
                    
                    if check.status == "approved":
                        print(f"  ✅ Code verified successfully!")
                    else:
                        print(f"  ❌ Verification failed. Status: {check.status}")
            else:
                print(f"  ❌ Failed to send. Status: {verification.status}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        return False


def test_sms():
    """Test SMS sending."""
    print("💬 Testing SMS sending...\n")
    
    if not settings.TWILIO_FROM_NUMBER:
        print("  ⚠️  TWILIO_FROM_NUMBER not set. Skipping SMS test.")
        print("     Add a phone number in your .env to test SMS.\n")
        return True
    
    try:
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        print(f"  From number: {settings.TWILIO_FROM_NUMBER}")
        
        test_phone = input("  Enter phone number to send test SMS (or press Enter to skip): ").strip()
        
        if test_phone:
            if not test_phone.startswith("+"):
                print("  ⚠️  Phone should start with + (e.g., +16464171584)")
                return True
            
            print(f"  📤 Sending test SMS to {test_phone}...")
            
            message = client.messages.create(
                body="🧪 Test message from Alert311! If you're seeing this, SMS alerts work! 🎉",
                from_=settings.TWILIO_FROM_NUMBER,
                to=test_phone,
            )
            
            print(f"  ✅ SMS sent! Message SID: {message.sid}")
            print(f"     Status: {message.status}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
        
        # Check for common errors
        error_str = str(e).lower()
        if "unverified" in error_str:
            print("  💡 Tip: You're on a trial account. Verify the recipient number in Twilio Console,")
            print("     or upgrade your account to send to any number.")
        elif "invalid" in error_str and "from" in error_str:
            print("  💡 Tip: Check that TWILIO_FROM_NUMBER is correct and verified in Twilio.")
        
        print()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Twilio Configuration Test")
    print("=" * 70)
    print()
    
    creds_ok = test_credentials()
    
    if not creds_ok:
        print("❌ Please set missing credentials in your .env file")
        print("   See TWILIO_SETUP.md for instructions.\n")
        return 1
    
    verify_ok = test_verify_service()
    sms_ok = test_sms()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  Credentials: {'✅ OK' if creds_ok else '❌ FAIL'}")
    print(f"  Verify Service: {'✅ OK' if verify_ok else '❌ FAIL'}")
    print(f"  SMS Sending: {'✅ OK' if sms_ok else '❌ FAIL'}")
    print()
    
    if creds_ok and verify_ok and sms_ok:
        print("🎉 All tests passed! Twilio is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
