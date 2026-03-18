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




def process_media(path):
    initialize_db()
    ext = os.path.splitext(path)[1].lower()

    should_index, current_hash = should_process(path)
    if not should_index:
        print(f"Already indexed do Skipped : {path}")
        return

    if ext in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
        audio_path = extract_audio(path)
        file_name = get_file_name(path)
        duration = get_duration(path)
        if audio_path:
            transcript = transcribe_audio(audio_path)
            os.remove(audio_path)
            summary_text = summary_generator(transcript)
            
            media_id = save_to_db(path, file_name, duration, transcript, summary=summary_text, current_hash=current_hash)
            if media_id:
                save_to_vector_db(media_id, file_name, path, transcript, summary=summary_text)
                save_summary_vector(media_id, file_name, summary_text)
                index_video_visually(path, media_id)

    elif ext == ".pdf":
        
        process_pdf(path)

    elif ext in (".md", ".txt"):
        
        process_file(path)

    else:
        print(f"Unsupported file type: {ext}")

def process_job(job):
    job_id = job["id"]
    path = job["file_path"]

    try:
        update_job_status(job_id, "running", stage="checking", progress=5)

        ext = os.path.splitext(path)[1].lower()
        if ext in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
            update_job_status(job_id, "running", stage="media_pipeline", progress=20)
        elif ext == ".pdf":
            update_job_status(job_id, "running", stage="pdf_pipeline", progress=20)
        elif ext in (".md", ".txt"):
            update_job_status(job_id, "running", stage="doc_pipeline", progress=20)

        process_media(path)

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