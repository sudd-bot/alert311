"""
Vercel serverless function entry point for FastAPI.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# Vercel will look for this
handler = app
