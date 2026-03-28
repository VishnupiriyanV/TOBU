from datetime import datetime
import os
import sqlite3
import time

if __package__:
    from backend.search_and_index.aural_engine import extract_audio, get_duration, get_file_name, transcribe_audio
    from backend.search_and_index.document_engine import process_pdf, process_file
    from backend.search_and_index.semantic_engine import save_to_vector_db, save_summary_vector, semantic_search
    from backend.search_and_index.sql_database import (
        DATABASE_PATH,
        fetch_next_job,
        get_job_retries,
        increment_retry,
        requeue_job,
        reset_stale_running_jobs,
        save_to_db,
        search_to_json,
        should_process,
        update_job_status,
    )
    from backend.search_and_index.summarizer import summary_generator
    from backend.search_and_index.visual_engine import index_video_visually
else:
    from aural_engine import extract_audio, get_duration, get_file_name, transcribe_audio
    from document_engine import process_pdf, process_file
    from semantic_engine import save_to_vector_db, save_summary_vector, semantic_search
    from sql_database import (
        DATABASE_PATH,
        fetch_next_job,
        get_job_retries,
        increment_retry,
        requeue_job,
        reset_stale_running_jobs,
        save_to_db,
        search_to_json,
        should_process,
        update_job_status,
    )
    from summarizer import summary_generator
    from visual_engine import index_video_visually


def process_media(path, progress_cb=None):
    def progress(stage, pct):
        if progress_cb:
            progress_cb(stage, pct)

    ext = os.path.splitext(path)[1].lower()

    progress("checking_hash", 5)
    should_index, current_hash = should_process(path)
    if not should_index:
        progress("skipped_unchanged", 100)
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
            path,
            file_name,
            duration,
            transcript,
            summary=summary_text,
            current_hash=current_hash,
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
        print(f"[TOBU] Job {job_id}: {stage} ({pct}%)")
        update_job_status(job_id, "running", stage=stage, progress=pct)

    try:
        update_job_status(job_id, "running", stage="starting", progress=1)
        result = process_media(path, progress_cb=job_progress)

        if result == "skipped":
            update_job_status(
                job_id,
                "done",
                stage="skipped_unchanged",
                progress=100,
                error_message=None,
            )
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


def worker_loop(poll_interval=1.0, stop_flag=None):
    reset_stale_running_jobs()

    while True:
        if stop_flag and stop_flag():
            break
        job = fetch_next_job()
        if job is None:
            time.sleep(poll_interval)
            continue
        process_job(job)


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


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
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
    min_score=0.0,
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
            min_score,
        ):
            merged.append(row)

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:limit]
