from fastapi import APIRouter, HTTPException
from .api_models import EnvelopeSuccess
from . import api_service

router = APIRouter(prefix="/api/v1/media", tags=["Media"])

@router.get("/{media_id}", response_model=EnvelopeSuccess)
async def get_media_detail(media_id: int):
    return {"ok": True, "data": {"id": media_id, "status": "indexed"}}