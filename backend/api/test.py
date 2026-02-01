"""
Minimal test endpoint to verify Vercel deployment works.
"""
from mangum import Mangum
from fastapi import FastAPI

test_app = FastAPI()

@test_app.get("/")
def read_root():
    return {"status": "ok", "message": "Vercel deployment works!"}

@test_app.get("/health")
def health():
    return {"status": "healthy"}

handler = Mangum(test_app, lifespan="off")
