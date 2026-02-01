#!/usr/bin/env python3
"""
Simple Twilio test without app dependencies.
"""
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")
FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

print("=" * 70)
print("Twilio Quick Test")
print("=" * 70)
print()

# Check credentials
print("🔍 Checking credentials...")
print(f"  Account SID: {ACCOUNT_SID[:10] if ACCOUNT_SID else 'MISSING'}...")
print(f"  Auth Token: {AUTH_TOKEN[:10] if AUTH_TOKEN else 'MISSING'}...")
print(f"  Verify SID: {VERIFY_SID[:10] if VERIFY_SID else 'MISSING'}...")
print(f"  From Number: {FROM_NUMBER or 'MISSING'}")
print()

if not all([ACCOUNT_SID, AUTH_TOKEN, VERIFY_SID]):
    print("❌ Missing required credentials in .env file!")
    exit(1)

# Create client
try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    print("✅ Twilio client created successfully")
    print()
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    exit(1)

# Test Verify service
try:
    print("📱 Testing Verify service...")
    service = client.verify.v2.services(VERIFY_SID).fetch()
    print(f"  ✅ Verify service found: {service.friendly_name}")
    print(f"     SID: {service.sid}")
    print()
except Exception as e:
    print(f"  ❌ Error fetching verify service: {e}")
    exit(1)

# Test SMS capability (if FROM_NUMBER is set)
if FROM_NUMBER:
    print(f"💬 SMS sending capability ready")
    print(f"   From: {FROM_NUMBER}")
    print()
    
    test = input("Send a test SMS to yourself? (y/n): ").strip().lower()
    if test == 'y':
        to_number = input("Enter your phone number (e.g., +16464171584): ").strip()
        if to_number:
            try:
                message = client.messages.create(
                    body="🧪 Test from Alert311! Your Twilio setup is working! 🎉",
                    from_=FROM_NUMBER,
                    to=to_number
                )
                print(f"  ✅ SMS sent! Message SID: {message.sid}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
else:
    print("⚠️  TWILIO_FROM_NUMBER not set")

print()
print("=" * 70)
print("🎉 Twilio is configured and ready to use!")
print("=" * 70)
