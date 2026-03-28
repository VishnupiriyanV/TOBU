from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
import sys
import subprocess
import urllib.parse
from pathlib import Path
from pydantic import BaseModel
from .api_models import EnvelopeSuccess
from . import api_service

user_added_dirs = set()

class OpenMediaRequest(BaseModel):
    file_path: str

router = APIRouter(prefix="/api/v1/media", tags=["Media"])

@router.get("/serve", response_class=FileResponse)
async def serve_file(file_path: str = Query(..., description="Absolute or relative path to the file to serve")):
    # 1. Decode URL safely
    decoded_path = urllib.parse.unquote(file_path)
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    watch_dir = base_dir / "watch"
    
    ALLOWED_BASE_DIRS = [watch_dir.resolve()] + [Path(d).resolve() for d in user_added_dirs]
    
    path_obj = Path(decoded_path)
    if not path_obj.is_absolute():
        path_obj = watch_dir / path_obj
        
    resolved_path = path_obj.resolve()
    
    # Security check: must start with one of the ALLOWED_BASE_DIRS
    is_allowed = False
    for base in ALLOWED_BASE_DIRS:
        try:
            resolved_path.relative_to(base)
            is_allowed = True
            break
        except ValueError:
            continue
            
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Forbidden: Path not in allowed directories")
        
    # File existence check
    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {resolved_path}")
        
    media_type = "application/pdf" if resolved_path.suffix.lower() == ".pdf" else None
    headers = {}
    if media_type == "application/pdf":
        headers["Content-Disposition"] = f'inline; filename="{resolved_path.name}"'
        
    return FileResponse(resolved_path, media_type=media_type, headers=headers)


@router.post("/open", response_model=EnvelopeSuccess)
async def open_media_native(payload: OpenMediaRequest):
    decoded_path = urllib.parse.unquote(payload.file_path)
    
    ALLOWED_BASE_DIRS = [watch_dir.resolve()] + [Path(d).resolve() for d in user_added_dirs]
    
    path_obj = Path(decoded_path)
    if not path_obj.is_absolute():
        path_obj = watch_dir / path_obj
        
    resolved_path = path_obj.resolve()
    
    is_allowed = False
    for base in ALLOWED_BASE_DIRS:
        try:
            resolved_path.relative_to(base)
            is_allowed = True
            break
        except ValueError:
            continue
            
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Forbidden: Path not in allowed directories")
        
    # File existence check
    if not resolved_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {resolved_path}")
        
    try:
        if os.name == 'nt':
            os.startfile(resolved_path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', resolved_path], check=True)
        else:
            subprocess.run(['xdg-open', resolved_path], check=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"ok": True, "data": {"message": "Opened successfully"}}

class AllowDirRequest(BaseModel):
    directory_path: str

@router.post("/allow-dir")
async def allow_directory(payload: AllowDirRequest):
    p = Path(payload.directory_path).resolve()
    if p.is_dir():
        user_added_dirs.add(str(p))
        return {"ok": True}
    raise HTTPException(status_code=400, detail="Invalid directory")


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