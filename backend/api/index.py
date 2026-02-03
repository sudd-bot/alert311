"""
Vercel serverless entry point for FastAPI.
"""
import sys
import os
from pathlib import Path

# Add parent directory (backend) to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from mangum import Mangum
    from app.main import app
    
    # Mangum adapter for Vercel
    handler = Mangum(app, lifespan="off")
    
except ImportError as e:
    # Import error - return diagnostic
    import json
    import traceback
    
    def handler(event, context=None):
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Import failed',
                'message': str(e),
                'trace': traceback.format_exc(),
                'sys_path': sys.path[:5],
                'backend_dir': str(backend_dir),
                'backend_exists': backend_dir.exists()
            }, indent=2)
        }

except Exception as e:
    # Other error - return diagnostic
    import json
    import traceback
    
    def handler(event, context=None):
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Initialization failed',
                'message': str(e),
                'trace': traceback.format_exc(),
                'env_vars': {k: 'SET' for k in os.environ if 'TWILIO' in k or 'DATABASE' in k or 'CRON' in k}
            }, indent=2)
        }
