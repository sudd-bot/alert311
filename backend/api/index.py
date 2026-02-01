"""
Vercel serverless entry point for FastAPI.
"""
from mangum import Mangum
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

handler = Mangum(app, lifespan="off")
