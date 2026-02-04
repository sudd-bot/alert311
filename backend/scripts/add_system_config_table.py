#!/usr/bin/env python3
"""
Add system_config table to existing database.
Run this once to add the new table without dropping existing data.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from app.models.system_config import SystemConfig
from app.models.base import Base

if __name__ == "__main__":
    print("Adding system_config table to database...")
    
    # Create only the SystemConfig table (won't affect existing tables)
    SystemConfig.__table__.create(engine, checkfirst=True)
    
    print("✓ system_config table created successfully!")
    print("  Table: system_config")
    print("  Columns: key (primary), value, created_at, updated_at, last_updated_timestamp")
