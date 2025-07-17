"""
Base router for the API.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def api_root():
    """
    Root endpoint for the API.
    """
    return {
        "message": "Local Music Generator API",
        "version": "0.1.0",
        "status": "operational"
    }