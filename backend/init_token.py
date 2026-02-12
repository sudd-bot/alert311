#!/usr/bin/env python3
"""
One-time script to initialize system SF 311 token from reporter credentials.
"""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal, init_db
from app.models import SystemConfig

# Initialize database
init_db()

# Read reporter token
reporter_env = Path(__file__).parent.parent.parent / "reporter" / ".env"
with open(reporter_env) as f:
    lines = f.readlines()

token_data = {}
for line in lines:
    line = line.strip()
    if line.startswith("access_token="):
        token_data["access_token"] = line.split("=", 1)[1]
    elif line.startswith("refresh_token="):
        token_data["refresh_token"] = line.split("=", 1)[1]
    elif line.startswith("expires_in="):
        token_data["expires_in"] = int(line.split("=", 1)[1])
    elif line.startswith("obtained_at="):
        token_data["obtained_at"] = int(line.split("=", 1)[1])

print(f"Loaded token data from reporter: expires_in={token_data['expires_in']}s")

# Insert into database
db = SessionLocal()
try:
    # Check if system token already exists
    existing = db.query(SystemConfig).filter(
        SystemConfig.key == "sf311_system_token"
    ).first()
    
    if existing:
        print("System token already exists, updating...")
        existing.value = json.dumps(token_data)
        existing.last_updated_timestamp = token_data["obtained_at"]
    else:
        print("Creating new system token...")
        config = SystemConfig(
            key="sf311_system_token",
            value=json.dumps(token_data),
            last_updated_timestamp=token_data["obtained_at"],
        )
        db.add(config)
    
    db.commit()
    print("✓ System SF 311 token initialized successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
    raise
finally:
    db.close()
