"""
Portal Routes (placeholder)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/episodes")
async def list_episodes():
    """List all episodes"""
    return {"episodes": []}
