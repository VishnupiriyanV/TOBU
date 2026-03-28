from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading

from .api_routes_system import router as system_router
from .api_routes_jobs import router as jobs_router
from .api_routes_search import router as search_router
from .api_routes_ingest import router as ingest_router
from .api_routes_media import router as media_router
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
DEFAULT_WATCH_FOLDER = os.environ.get(
    "TOBU_WATCH_FOLDER",
    os.path.join(PROJECT_ROOT, "watch"),
)

_stop_worker = False
_watcher_observer = None

def _worker_stop_flag():
    return _stop_worker

def get_observer():
    global _watcher_observer
    return _watcher_observer


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _stop_worker, _watcher_observer
    _stop_worker = False
    worker_thread = None
    _watcher_observer = None

    # Start the runtime worker loop in a background daemon thread
    try:
        from . import sql_database
        sql_database.initialize_db()
        from . import runtime_service
        worker_thread = threading.Thread(
            target=runtime_service.worker_loop,
            kwargs={"poll_interval": 1.0, "stop_flag": _worker_stop_flag},
            daemon=True,
            name="tobu-worker",
        )
        worker_thread.start()
        print("[TOBU] Runtime worker started (background thread)")
    except Exception as e:
        print(f"[TOBU] Warning: Could not start runtime worker: {e}")
        print("[TOBU] API server running without auto-processing (install dependencies to enable)")

    try:
        from .watch import FileHandler, initial_scan
        from watchdog.observers import Observer

        watch_folder = DEFAULT_WATCH_FOLDER
        os.makedirs(watch_folder, exist_ok=True)
        _watcher_observer = Observer()
        _watcher_observer.schedule(FileHandler(), watch_folder, recursive=True)
        _watcher_observer.start()
        initial_scan(watch_folder)
        print(f"[TOBU] File watcher active on: {watch_folder}")
    except Exception as e:
        print(f"[TOBU] Warning: Could not start file watcher: {e}")
        observer = None

    yield  # App is running

    # Shutdown: signal the worker to stop
    if _watcher_observer:
        _watcher_observer.stop()
        _watcher_observer.join(timeout=5)
    _stop_worker = True
    if worker_thread and worker_thread.is_alive():
        worker_thread.join(timeout=5)
        print("[TOBU] Runtime worker stopped")


app = FastAPI(title="TOBU Indexing API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(jobs_router)
app.include_router(search_router)
app.include_router(ingest_router)
app.include_router(media_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "ok" in detail and "error" in detail:
        content = detail
    else:
        content = {
            "ok": False,
            "error": {
                "code": f"http_{exc.status_code}",
                "message": str(detail)
            }
        }
    return JSONResponse(status_code=exc.status_code, content=content)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred."
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)