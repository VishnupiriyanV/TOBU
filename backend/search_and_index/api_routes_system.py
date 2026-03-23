from fastapi import APIRouter, HTTPException
from .api_models import EnvelopeSuccess, EnvelopeError, ErrorBody
from . import api_service

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