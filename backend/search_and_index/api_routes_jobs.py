from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .api_models import EnvelopeSuccess, JobItem
from . import api_service

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.get("/", response_model=EnvelopeSuccess[dict])
async def list_jobs(
    status: Optional[str] = Query(None, pattern="^(queued|running|failed|done|cancelled)$"),
    limit: int = Query(100, ge=1, le=500)
):
    
    jobs = api_service.get_jobs(status=status, limit=limit)
    return {"ok": True, "data": {"count": len(jobs), "items": jobs}}

@router.get("/{job_id}", response_model=EnvelopeSuccess[JobItem])
async def get_job(job_id: int):
    """Get details for a specific job."""
    job = api_service.get_job_or_none(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, "data": job}

@router.post("/{job_id}/retry", response_model=EnvelopeSuccess)
async def retry_job(job_id: int):
    """Retry a failed or cancelled job."""
    success = api_service.retry_job_by_id(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or not in a retryable state")
    return {"ok": True, "data": {"job_id": job_id, "retried": True}}

@router.post("/{job_id}/cancel", response_model=EnvelopeSuccess)
async def cancel_job(job_id: int):

    success = api_service.cancel_job_by_id(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already finished")
    return {"ok": True, "data": {"job_id": job_id, "cancelled": True}}