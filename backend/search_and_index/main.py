from aural_engine import extract_audio,get_duration,get_file_name,transcribe_audio
from sql_database import (
    save_to_db, initialize_db, should_process,
    fetch_next_job, update_job_status, increment_retry, get_job_retries,
    requeue_job, reset_stale_running_jobs
)

from semantic_engine import save_to_vector_db, save_summary_vector
from document_engine import process_pdf, process_file
from summarizer import summary_generator
from visual_engine import index_video_visually
import warnings
import time
import os

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


if __name__ == "__main__":
    worker_loop()