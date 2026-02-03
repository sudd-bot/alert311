#!/usr/bin/env python3
"""Check SMS delivery status from Twilio."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from twilio.rest import Client
from app.core.config import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# Check the message we just sent
message_sid = "SMca4c8368c6f2693d94cae1997a995462"

message = client.messages(message_sid).fetch()

print(f"Message SID: {message.sid}")
print(f"Status: {message.status}")
print(f"To: {message.to}")
print(f"From: {message.from_}")
print(f"Body: {message.body[:50]}...")
print(f"Error Code: {message.error_code}")
print(f"Error Message: {message.error_message}")
print(f"Date Created: {message.date_created}")
print(f"Date Updated: {message.date_updated}")
print(f"Date Sent: {message.date_sent}")
