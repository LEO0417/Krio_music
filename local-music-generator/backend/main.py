"""
Main entry point for the Local Music Generator API.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import API_V1_PREFIX, CORS_ORIGINS, DEBUG

# Create FastAPI app
app = FastAPI(
    title="Local Music Generator API",
    description="API for generating music using Facebook's MusicGen model locally",
    version="0.1.0",
    debug=DEBUG,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Local Music Generator API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# Include API routers here
from api.base import router as base_router
app.include_router(base_router, prefix=API_V1_PREFIX)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)