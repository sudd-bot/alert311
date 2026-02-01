#!/usr/bin/env python3
"""Test SMS alert sending."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.sms_alert import sms_alert_service

# Test report data
test_report = {
    "id": "test-123",
    "ticket_type_name": "Parking on Sidewalk",
    "address": "123 Market St, San Francisco",
    "description": "Car parked on sidewalk blocking pedestrian access",
    "created_at": "2026-02-01T08:00:00Z"
}

print("Sending test SMS alert...")
success = sms_alert_service.send_alert(
    to_phone="+16464171584",
    report_data=test_report
)

if success:
    print("✅ SMS sent successfully!")
else:
    print("❌ SMS failed to send")
