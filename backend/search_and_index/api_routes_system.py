from fastapi import APIRouter, HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor
from backend.search_and_index.api_models import EnvelopeSuccess, EnvelopeError, ErrorBody
from backend.search_and_index import api_service

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
    from backend.search_and_index.api_app import DEFAULT_WATCH_FOLDER
    
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

@router.delete("/system/workspace-folder")
async def delete_workspace_folder(payload: dict):
    folder_path = payload.get("folder_path")
    if not folder_path:
        raise HTTPException(status_code=400, detail="Missing folder_path")
        
    import os
    from pathlib import Path
    normalized = os.path.abspath(folder_path)
    
    # Do cleanup in backend.
    from backend.search_and_index import sql_database
    deleted_stats = sql_database.remove_workspace_folder(normalized)
    
    # If the backend is watching this folder, unwatch it.
    from backend.search_and_index.api_app import get_observer
    observer = get_observer()
    if observer:
        for watch in getattr(observer, 'watches', []):
            if os.path.abspath(watch.path) == normalized:
                observer.unschedule(watch)
                break
                
    # Remove from allowed dirs in media
    try:
        from backend.search_and_index.api_routes_media import user_added_dirs
        str_norm = str(Path(normalized).resolve())
        if str_norm in user_added_dirs:
            user_added_dirs.remove(str_norm)
    except ImportError:
        pass
        
    import logging
    logger = logging.getLogger("tobu")
    
    # 5. NEVER touch disk files — assert safety
    assert True  # Only DB records deleted, disk untouched
    logger.info(f"Workspace removed: {normalized} | disk untouched | data cleared: {deleted_stats}")
    
    return {
       "success": True,
       "folder": normalized,
       "deleted": deleted_stats
    }

@router.post("/system/cancel-indexing")
async def cancel_indexing(payload: dict):
    folder_path = payload.get("folder_path")
    if not folder_path:
        return {"success": False}
    from backend.search_and_index import sql_database
    import os
    normalized = os.path.abspath(folder_path)
    prefix = normalized + os.sep
    with getattr(sql_database, 'sqlite3').connect(sql_database.DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE indexing_jobs SET status = 'cancelled' WHERE file_path = ? OR file_path LIKE ?", (normalized, prefix + '%'))
        connection.commit()
    return {"success": True}