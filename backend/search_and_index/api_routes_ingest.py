from fastapi import APIRouter
from pydantic import BaseModel

from .api_models import EnvelopeSuccess
from . import api_service

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingest"])


class FileIngestRequest(BaseModel):
	file_path: str
	source_type: str = "video"
	max_retries: int = 3


@router.post("/file", response_model=EnvelopeSuccess)
async def ingest_file(req: FileIngestRequest):
	data = api_service.ingest_file(req.file_path, req.source_type, req.max_retries)
	return {"ok": True, "data": data}


@router.delete("/file", response_model=EnvelopeSuccess)
async def delete_file(file_path: str):
	api_service.delete_file(file_path)
	return {"ok": True, "data": {"deleted": True}}

