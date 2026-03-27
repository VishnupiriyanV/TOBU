from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
import urllib.parse
from pathlib import Path
from .api_models import EnvelopeSuccess
from . import api_service

router = APIRouter(prefix="/api/v1/media", tags=["Media"])

@router.get("/serve", response_class=FileResponse)
async def serve_file(file_path: str = Query(..., description="Absolute or relative path to the file to serve")):
    # 1. Decode URL safely
    decoded_path = urllib.parse.unquote(file_path)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    watch_dir = base_dir / "watch"
    
    path_obj = Path(decoded_path)
    if not path_obj.is_absolute():
        path_obj = watch_dir / path_obj
        
    resolved_path = path_obj.resolve()
    
    # Security check: must be inside the watch_dir
    try:
        resolved_path.relative_to(watch_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Forbidden: Path must be within watch directory")
        
    # File existence check
    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {resolved_path}")
        
    media_type = "application/pdf" if resolved_path.suffix.lower() == ".pdf" else None
    return FileResponse(resolved_path, media_type=media_type)


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