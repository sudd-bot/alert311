#!/usr/bin/env python3
"""Check recent SMS messages from Twilio."""
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# Get last 5 messages
messages = client.messages.list(limit=5)

for msg in messages:
    print(f"\nMessage SID: {msg.sid}")
    print(f"Status: {msg.status}")
    print(f"To: {msg.to}")
    print(f"From: {msg.from_}")
    print(f"Body: {msg.body[:80]}...")
    print(f"Error Code: {msg.error_code}")
    print(f"Date Created: {msg.date_created}")
    print(f"Date Sent: {msg.date_sent}")
    print("-" * 60)
