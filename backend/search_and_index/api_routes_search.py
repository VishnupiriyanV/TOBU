from fastapi import APIRouter
from typing import List
from .api_models import EnvelopeSuccess, HybridSearchRequest, HybridResultItem
from . import api_service

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

@router.post("/hybrid", response_model=EnvelopeSuccess[dict])
async def search_hybrid(payload: HybridSearchRequest):
    """hybrid search """
    results = api_service.search_hybrid(payload)
    return {
        "ok": True, 
        "data": {
            "query": payload.query,
            "count": len(results),
            "items": results
        }
    }

@router.post("/semantic", response_model=EnvelopeSuccess[dict])
async def search_semantic_endpoint(query: str, limit: int = 20):
    results = api_service.search_semantic(query, limit)
    return {"ok": True, "data": {"count": len(results), "items": results}}

@router.post("/keyword", response_model=EnvelopeSuccess[dict])
async def search_keyword_endpoint(query: str):
    results = api_service.search_keyword(query)
    return {"ok": True, "data": {"count": len(results), "items": results}}