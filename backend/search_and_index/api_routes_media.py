from fastapi import APIRouter, HTTPException
from .api_models import EnvelopeSuccess
from . import api_service

router = APIRouter(prefix="/api/v1/media", tags=["Media"])

@router.get("/{media_id}", response_model=EnvelopeSuccess)
async def get_media_detail(media_id: int):
    item = api_service.get_media_detail(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"ok": True, "data": item}


@router.get("/{media_id}/segments", response_model=EnvelopeSuccess)
async def get_media_segments(media_id: int, limit: int = 200):
    item = api_service.get_media_detail(media_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Media not found")
    segments = api_service.get_media_segments(media_id, limit=limit)
    return {"ok": True, "data": {"count": len(segments), "items": segments}}