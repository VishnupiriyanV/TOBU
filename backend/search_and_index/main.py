from aural_engine import extract_audio,get_duration,get_file_name,transcribe_audio
from sql_database import save_to_db, search_to_json, initialize_db,DATABASE_PATH,should_process
from semantic_engine import save_to_vector_db, save_summary_vector
from document_engine import process_pdf, process_file
import sqlite3
from summarizer import summary_generator
from visual_engine import index_video_visually
import warnings
import time
import os

warnings.filterwarnings("ignore")




def process_media(path):
    ext = os.path.splitext(path)[1].lower()

    if not should_process(path):
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
            initialize_db()
            media_id = save_to_db(path, file_name, duration, transcript, summary=summary_text)
            if media_id:
                save_to_vector_db(media_id, file_name, path, transcript, summary=summary_text)
                save_summary_vector(media_id, file_name, summary_text)
                index_video_visually(path, media_id)

    elif ext == ".pdf":
        initialize_db()
        process_pdf(path)

    elif ext in (".md", ".txt"):
        initialize_db()
        process_file(path)

    else:
        print(f"Unsupported file type: {ext}")


if __name__ == "__main__":
    
    path = "C:/Helm/FossHack/TOBU/test3.mp4"

    start = time.time()
    process_media(path)
    end = time.time()
    print("Execution time:", end - start)