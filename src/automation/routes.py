"""
Automation Routes (placeholder)
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def trigger_generation():
    """Trigger episode generation"""
    return {"status": "queued"}
