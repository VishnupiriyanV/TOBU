from typing import List, Optional, Dict, Any
import os

if __package__:
    from . import sql_database
else:
    import sql_database


def _get_runtime_service():
    if __package__:
        from . import runtime_service as _runtime_service
    else:
        import runtime_service as _runtime_service
    return _runtime_service


def _get_raw_semantic_search():
    if __package__:
        from .semantic_engine import semantic_search as _raw_semantic_search
    else:
        from semantic_engine import semantic_search as _raw_semantic_search
    return _raw_semantic_search

#converts to api standard 
def normalize_result_item(item: Dict[Any, Any]) -> Dict[str, Any]:
    return {
        "file_name": item.get("file_name") or item.get("file-name"),
        "file_path": item.get("file_path") or item.get("file-path"),
        "start": item.get("start"),
        "end": item.get("end"),
        "text": item.get("text"),
        "score": item.get("score", 0.0),
        "matched_by": item.get("matched_by") or item.get("matched-by", []),
        "semantic_rank": item.get("semantic_rank"),
        "keyword_rank": item.get("keyword_rank"),
        "source_type": item.get("source_type"),
        "added_at": item.get("added_at")
    }

def health_status() -> Dict[str, str]:
    try:
        sql_database.initialize_db()
        return {"status": "up", "database": "ok"}
    except Exception:
        return {"status": "error", "database": "fail"}

def get_jobs(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    return sql_database.list_jobs(status=status, limit=limit)

def get_job_or_none(job_id: int) -> Optional[Dict[str, Any]]:
    return sql_database.get_job(job_id)

def retry_job_by_id(job_id: int) -> bool:
    return sql_database.retry_job(job_id)

def cancel_job_by_id(job_id: int) -> bool:
    return sql_database.cancel_job(job_id)

def search_hybrid(payload: Any) -> List[Dict[str, Any]]:
    runtime_service = _get_runtime_service()
    raw_results = runtime_service.hybrid_search_rrf(
        query=payload.query,
        limit=payload.limit,
        semantic_limit=payload.semantic_limit,
        keyword_limit=payload.keyword_limit,
        k=payload.k,
        source_types=payload.source_types,
        folders=payload.folders,
        date_from=payload.date_from,
        date_to=payload.date_to,
        min_score=payload.min_score
    )
    return [normalize_result_item(r) for r in raw_results]



def search_semantic(query: str, limit: int) -> List[Dict[str, Any]]:
    raw_semantic_search = _get_raw_semantic_search()
    results = raw_semantic_search(query, limit) or []
    return [normalize_result_item(r) for r in results]

def search_keyword(query: str) -> List[Dict[str, Any]]:
    results = sql_database.search_to_json(query) or []
    return [normalize_result_item(r) for r in results]

def ingest_file(file_path: str, source_type: Optional[str] = None, max_retries: int = 3) -> Dict[str, Any]:
    job_id, created = sql_database.enqueue_job(file_path, source_type, max_retries)
    return {"job_id": job_id, "created": created}

def ingest_folder(folder_path: str, recursive: bool = True) -> Dict[str, int]:
    supported_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".pdf", ".md", ".txt"}
    queued_count = 0
    skipped_count = 0
    
    for root, _, files in os.walk(folder_path):
        if not recursive and root != folder_path:
            continue
        for file in files:
            if os.path.splitext(file)[1].lower() in supported_exts:
                _, created = sql_database.enqueue_job(os.path.join(root, file))
                if created: queued_count += 1
                else: skipped_count += 1
    
    return {"queued": queued_count, "skipped_duplicates": skipped_count}

def reindex_file(file_path: str) -> Dict[str, Any]:
    sql_database.cancel_jobs_for_path(file_path)
    sql_database.delete_file_records(file_path)
    return ingest_file(file_path)

def delete_file(file_path: str):
    sql_database.cancel_jobs_for_path(file_path)
    sql_database.delete_file_records(file_path)


def get_media_detail(media_id: int) -> Optional[Dict[str, Any]]:
    return sql_database.get_media_detail(media_id)


def get_media_segments(media_id: int, limit: int = 200) -> List[Dict[str, Any]]:
    return sql_database.get_media_segments(media_id, limit=limit)


def system_status() -> Dict[str, Any]:
    return {
        "health": health_status(),
        "db_stats": sql_database.get_db_stats(),
    }


def run_integrity_check() -> Dict[str, Any]:
    return sql_database.integrity_check()


def create_backup(label: Optional[str] = None) -> Dict[str, Any]:
    return sql_database.create_backup(label=label)