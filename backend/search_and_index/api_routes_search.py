from fastapi import APIRouter, Query
from typing import List
from backend.search_and_index.api_models import EnvelopeSuccess, HybridSearchRequest, HybridResultItem
from backend.search_and_index import api_service

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
async def search_semantic_endpoint(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=200)
):
    results = api_service.search_semantic(query, limit)
    return {"ok": True, "data": {"count": len(results), "items": results}}

@router.post("/keyword", response_model=EnvelopeSuccess[dict])
async def search_keyword_endpoint(query: str = Query(..., min_length=1)):
    results = api_service.search_keyword(query)
    return {"ok": True, "data": {"count": len(results), "items": results}}


@router.post("/visual", response_model=EnvelopeSuccess[dict])
async def search_visual_endpoint(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
):
    """Search video frames using CLIP visual embeddings."""
    results = api_service.search_visual(query, limit)
    return {"ok": True, "data": {"query": query, "count": len(results), "items": results}}