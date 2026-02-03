#!/usr/bin/env python3
"""Test SMS alert sending."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from twilio.rest import Client
from app.core.config import settings

# Test with direct Twilio client for debugging
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# Test report data
test_message = """🚨 Alert311: New Parking on Sidewalk report

📍 123 Market St, San Francisco
📝 Car parked on sidewalk blocking pedestrian access
🕐 2026-02-01T08:00:00Z

Report ID: test-123"""

print(f"Sending SMS to: +16464171584")
print(f"From: {settings.TWILIO_FROM_NUMBER}")
print(f"Message preview:\n{test_message}\n")

try:
    message = client.messages.create(
        body=test_message,
        from_=settings.TWILIO_FROM_NUMBER,
        to="+16464171584"
    )
    print(f"✅ SMS sent!")
    print(f"   Message SID: {message.sid}")
    print(f"   Status: {message.status}")
    print(f"   To: {message.to}")
    print(f"   From: {message.from_}")
except Exception as e:
    print(f"❌ Error: {e}")
