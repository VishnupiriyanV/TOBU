from fastapi import APIRouter, HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .api_models import EnvelopeSuccess, EnvelopeError, ErrorBody
from . import api_service

executor = ThreadPoolExecutor(max_workers=1)

def _prompt_file():
    import tkinter as tk
    from tkinter import filedialog
    import os
    # Provide a hidden window for the dialog
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(parent=root, title="Select File")
    root.destroy()
    return path

def _prompt_folder():
    import tkinter as tk
    from tkinter import filedialog
    import os
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askdirectory(parent=root, title="Select Folder")
    root.destroy()
    return path

router = APIRouter(prefix="/api/v1")

@router.get("/health", response_model=EnvelopeSuccess)
async def get_health():
   
    status = api_service.health_status()
    if status["database"] != "ok":
        # Map DB failures to 503 Service Unavailable 
        raise HTTPException(
            status_code=503, 
            detail={"ok": False, "error": {"code": "db_error", "message": "Database unreachable"}}
        )
    return {"ok": True, "data": status}

@router.get("/system/status", response_model=EnvelopeSuccess)
async def get_system_status():
    return {"ok": True, "data": api_service.system_status()}


@router.get("/system/integrity", response_model=EnvelopeSuccess)
async def get_integrity():
    return {"ok": True, "data": api_service.run_integrity_check()}


@router.post("/system/backup", response_model=EnvelopeSuccess)
async def create_backup(label: str | None = None):
    return {"ok": True, "data": api_service.create_backup(label=label)}

@router.get("/system/browse-file", response_model=EnvelopeSuccess)
async def system_browse_file():
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(executor, _prompt_file)
    return {"ok": True, "data": {"path": path or ""}}

@router.get("/system/browse-folder", response_model=EnvelopeSuccess)
async def system_browse_folder():
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(executor, _prompt_folder)
    return {"ok": True, "data": {"path": path or ""}}

def _build_file_tree(dir_path: str, base_dir: str) -> list:
    import os
    import mimetypes
    from datetime import datetime, timezone
    tree = []
    try:
        entries = sorted(os.scandir(dir_path), key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            if entry.name.startswith('.'):
                continue
            
            abs_path = os.path.abspath(entry.path).replace("\\", "/")    
            if entry.is_dir():
                tree.append({
                    "name": entry.name,
                    "type": "folder",
                    "path": abs_path,
                    "children": _build_file_tree(entry.path, base_dir)
                })
            else:
                mime_type, _ = mimetypes.guess_type(entry.name)
                stat = entry.stat()
                mtime_iso = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                
                tree.append({
                    "name": entry.name,
                    "type": "file",
                    "path": abs_path,
                    "mimeType": mime_type or "application/octet-stream",
                    "size": stat.st_size,
                    "lastModified": mtime_iso.replace('+00:00', 'Z')
                })
    except PermissionError:
        pass
    return tree

@router.get("/system/file-tree", response_model=EnvelopeSuccess)
async def get_system_file_tree():
    import os
    from .api_app import DEFAULT_WATCH_FOLDER
    
    if not os.path.exists(DEFAULT_WATCH_FOLDER):
        os.makedirs(DEFAULT_WATCH_FOLDER, exist_ok=True)
        
    tree = _build_file_tree(DEFAULT_WATCH_FOLDER, DEFAULT_WATCH_FOLDER)
    abs_watch = os.path.abspath(DEFAULT_WATCH_FOLDER).replace("\\", "/")
    
    root_node = {
        "name": os.path.basename(abs_watch) or "watch",
        "type": "folder",
        "path": abs_watch,
        "children": tree
    }
    
    return {"ok": True, "data": root_node}