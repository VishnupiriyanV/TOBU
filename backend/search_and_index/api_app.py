from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .api_routes_system import router as system_router
from .api_routes_jobs import router as jobs_router
from .api_routes_search import router as search_router
from .api_routes_ingest import router as ingest_router
from .api_routes_media import router as media_router

app = FastAPI(title="TOBU Indexing API", version="1.0.0")

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