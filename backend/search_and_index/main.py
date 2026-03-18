from aural_engine import extract_audio,get_duration,get_file_name,transcribe_audio
from sql_database import (
    save_to_db, initialize_db, should_process,
    fetch_next_job, update_job_status, increment_retry, get_job_retries,
    requeue_job, reset_stale_running_jobs,search_to_json, DATABASE_PATH
)

from semantic_engine import save_to_vector_db, save_summary_vector,semantic_search
from document_engine import process_pdf, process_file
from summarizer import summary_generator
from visual_engine import index_video_visually
import warnings
import time
import os
import sqlite3
from datetime import datetime

warnings.filterwarnings("ignore")




def process_media(path, progress_cb=None):
    def progress(stage, pct):
        if progress_cb:
            progress_cb(stage, pct)

    initialize_db()
    ext = os.path.splitext(path)[1].lower()

    progress("checking_hash", 5)
    should_index, current_hash = should_process(path)
    if not should_index:
        progress("skipped_unchanged", 100)
        print(f"Already indexed so skipped: {path}")
        return "skipped"

    if ext in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
        progress("extract_audio", 15)
        audio_path = extract_audio(path)
        if not audio_path:
            raise RuntimeError("Audio extraction failed")

        file_name = get_file_name(path)

        progress("read_duration", 22)
        duration = get_duration(path)

        progress("transcribing", 45)
        transcript = transcribe_audio(audio_path)

        progress("cleanup_temp_audio", 50)
        if os.path.exists(audio_path):
            os.remove(audio_path)

        progress("summarizing", 65)
        summary_text = summary_generator(transcript)

        progress("save_sql", 75)
        media_id = save_to_db(
            path, file_name, duration, transcript,
            summary=summary_text, current_hash=current_hash
        )
        if not media_id:
            raise RuntimeError("Failed to save media record")

        progress("save_semantic_vectors", 85)
        save_to_vector_db(media_id, file_name, path, transcript, summary=summary_text)

        progress("save_summary_vector", 90)
        save_summary_vector(media_id, file_name, summary_text)

        progress("index_visual_frames", 97)
        index_video_visually(path, media_id)

        progress("finished", 100)
        return "done"

    if ext == ".pdf":
        progress("process_pdf", 20)
        process_pdf(path)
        progress("finished", 100)
        return "done"

    if ext in (".md", ".txt"):
        progress("process_text", 20)
        process_file(path)
        progress("finished", 100)
        return "done"

    raise RuntimeError(f"Unsupported file type: {ext}")

def process_job(job):
    job_id = job["id"]
    path = job["file_path"]

    def job_progress(stage, pct):
        update_job_status(job_id, "running", stage=stage, progress=pct)

    try:
        update_job_status(job_id, "running", stage="starting", progress=1)
        result = process_media(path, progress_cb=job_progress)

        if result == "skipped":
            update_job_status(job_id, "done", stage="skipped_unchanged", progress=100, error_message=None)
        else:
            update_job_status(job_id, "done", stage="finished", progress=100, error_message=None)

    except Exception as e:
        increment_retry(job_id)
        retries, max_retries = get_job_retries(job_id)

        if retries < max_retries:
            update_job_status(job_id, "queued", stage="retrying", progress=0, error_message=str(e))
            requeue_job(job_id)
        else:
            update_job_status(job_id, "failed", stage="failed", progress=0, error_message=str(e))


def worker_loop(poll_interval=1.0):
    initialize_db()
    reset_stale_running_jobs()

    while True:
        job = fetch_next_job()
        if job is None:
            time.sleep(poll_interval)
            continue
        process_job(job)



#hybrid search helper funcs
def _result_key(item):
    file_path = os.path.abspath(item.get("file-path", ""))
    start = item.get("start")
    end = item.get("end")
    text = (item.get("text") or "").strip()
    return (file_path, start, end, text)

def _rrf_add(scores, ranks, items, source_name, k):
    for idx, item in enumerate(items, start=1):
        key = _result_key(item)
        scores[key] = scores.get(key, 0.0) + (1.0 / (k + idx))
        ranks.setdefault(key, {})[source_name] = idx

#to convert data to standard datetime
def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    # sqlite CURRENT_TIMESTAMP format - "YYYY-MM-DD HH:MM:SS"
    fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def _load_meta_by_paths(file_paths):
    if not file_paths:
        return {}
    #one query for full search
    abs_paths = [os.path.abspath(p) for p in file_paths]
    
    placeholders = ",".join(["?"] * len(abs_paths))
    query = f"""
        SELECT file_path, source_type, added_at
        FROM media_files
        WHERE file_path IN ({placeholders})
    """

    out = {}
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, tuple(abs_paths)).fetchall()
        for row in rows:
            out[os.path.abspath(row["file_path"])] = {
                "source_type": (row["source_type"] or "").lower(),
                "added_at": row["added_at"],
            }
    return out

def _passes_filters(item, source_types, folder_prefixes, date_from_dt, date_to_dt, min_score):
    if item["score"] < min_score:
        return False

    if source_types:
        if (item.get("source_type") or "").lower() not in source_types:
            return False

    if folder_prefixes:
        p = os.path.abspath(item.get("file-path", ""))
        if not any(p.startswith(prefix) for prefix in folder_prefixes):
            return False

    added_dt = _parse_date(item.get("added_at"))
    if date_from_dt and (added_dt is None or added_dt < date_from_dt):
        return False
    if date_to_dt and (added_dt is None or added_dt > date_to_dt):
        return False

    return True


def hybrid_search_rrf(
    query,
    limit=20,
    semantic_limit=40,
    keyword_limit=40,
    k=60,
    source_types=None,   
    folders=None,        
    date_from=None,      
    date_to=None,        
    min_score=0.0
):
    sem_results = semantic_search(query, semantic_limit) or []
    kw_results = (search_to_json(query) or [])[:keyword_limit]

    scores = {}
    ranks = {}
    payload = {}

    _rrf_add(scores, ranks, sem_results, "semantic", k)
    _rrf_add(scores, ranks, kw_results, "keyword", k)

    for item in sem_results + kw_results:
        key = _result_key(item)
        if key not in payload:
            payload[key] = {
                "file-name": item.get("file-name"),
                "file-path": os.path.abspath(item.get("file-path", "")),
                "start": item.get("start"),
                "end": item.get("end"),
                "text": item.get("text"),
            }

    meta_map = _load_meta_by_paths([v["file-path"] for v in payload.values()])

    normalized_source_types = set((s or "").lower() for s in (source_types or []))
    normalized_folders = [os.path.abspath(f) for f in (folders or [])]
    date_from_dt = _parse_date(date_from)
    date_to_dt = _parse_date(date_to)

    merged = []
    for key, base in payload.items():
        source_ranks = ranks.get(key, {})
        meta = meta_map.get(base["file-path"], {})

        row = {
            **base,
            "score": scores.get(key, 0.0),
            "matched_by": list(source_ranks.keys()),
            "semantic_rank": source_ranks.get("semantic"),
            "keyword_rank": source_ranks.get("keyword"),
            "source_type": meta.get("source_type"),
            "added_at": meta.get("added_at"),
        }

        if _passes_filters(
            row,
            normalized_source_types,
            normalized_folders,
            date_from_dt,
            date_to_dt,
            min_score
        ):
            merged.append(row)

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:limit]

if __name__ == "__main__":
    worker_loop()

#     results = hybrid_search_rrf(
#     query="water spilling in a cup",
#     limit=20,
#     source_types=["video", "pdf"],
#     folders=["C:/Helm/FossHack/TOBU/watch"],
#     date_from="2026-01-01",
#     min_score=0.01
# )