from fastapi import APIRouter
from pydantic import BaseModel

from backend.search_and_index.api_models import EnvelopeSuccess
from backend.search_and_index import api_service

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingest"])


class FileIngestRequest(BaseModel):
	file_path: str
	source_type: str = "video"
	max_retries: int = 3


class FolderIngestRequest(BaseModel):
	folder_path: str
	recursive: bool = True


class ReindexRequest(BaseModel):
	file_path: str


@router.post("/file", response_model=EnvelopeSuccess)
async def ingest_file(req: FileIngestRequest):
	data = api_service.ingest_file(req.file_path, req.source_type, req.max_retries)
	return {"ok": True, "data": data}


@router.delete("/file", response_model=EnvelopeSuccess)
async def delete_file(file_path: str):
	api_service.delete_file(file_path)
	return {"ok": True, "data": {"deleted": True}}


@router.post("/folder", response_model=EnvelopeSuccess)
async def ingest_folder(req: FolderIngestRequest):
	data = api_service.ingest_folder(req.folder_path, recursive=req.recursive)
	return {"ok": True, "data": data}


@router.post("/reindex", response_model=EnvelopeSuccess)
async def reindex_file(req: ReindexRequest):
	data = api_service.reindex_file(req.file_path)
	return {"ok": True, "data": data}

