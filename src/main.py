"""
AI Morning Podcast Portal - Main Application Entry Point
FastAPI application with modular architecture
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.common.config import get_settings
from src.portal import routes as portal_routes
from src.automation import routes as automation_routes

settings = get_settings()

app = FastAPI(
    title="AI Morning Podcast Portal",
    description="Daily AI news podcast generated automatically",
    version="1.0.0",
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [f"https://{settings.domain}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portal_routes.router, prefix="/api", tags=["portal"])
app.include_router(automation_routes.router, prefix="/api/automation", tags=["automation"])

# Static files (frontend)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "ai-morning-podcast"
    }

@app.get("/")
async def root():
    """Root endpoint - redirects to web portal"""
    return {"message": "AI Morning Podcast Portal API"}

if __name__ == "__main__":
    # Use 127.0.0.1 for local dev, 0.0.0.0 only in production
    host = "0.0.0.0" if not settings.debug else "127.0.0.1"
    uvicorn.run(
        "src.main:app",
        host=host,
        port=settings.port,
        reload=settings.debug
    )
