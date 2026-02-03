#!/usr/bin/env python3
"""Create a test report to trigger SMS alert."""
import sys
from sqlalchemy.orm import Session
from app.core.database import get_db, init_db
from app.models import Report

# Initialize database
init_db()

# Get database session
db = next(get_db())

# Create test report for alert_id=2 (336 Scott St)
test_report = Report(
    alert_id=2,
    report_id="TEST_" + str(int(__import__('time').time())),
    report_data={
        "id": "test-report-123",
        "address": "336 Scott St, San Francisco",
        "description": "Test 311 report - graffiti on building",
        "status": "Open",
        "created_at": "2026-02-01T00:00:00Z"
    },
    sms_sent=False
)

db.add(test_report)
db.commit()

print(f"✅ Created test report (ID: {test_report.id})")
print(f"   Alert ID: {test_report.alert_id}")
print(f"   Report ID: {test_report.report_id}")
print(f"   SMS Sent: {test_report.sms_sent}")
