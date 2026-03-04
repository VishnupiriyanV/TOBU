import ffmpeg
import json
import warnings
from faster_whisper import WhisperModel #needs cuda_12 toolkit for gpu
import time
import os
from sql_database import save_to_db, search_to_json, initialize_db
from semantic_engine import save_to_vector_db, save_summary_vector
import sqlite3
from summarizer import summary_generator



warnings.filterwarnings("ignore")



def extract_audio(input_path, output_path="temp.wav"):
    """converts to 16kHz mono WAV."""
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path
    except ffmpeg.Error as e:
        print(f"Error extracting audio: {e}")
        return None


def transcribe_audio(input_path, output_path="transcript.json"):
    model = WhisperModel("distil-large-v3", device="cuda", compute_type="int8")

    segments, info = model.transcribe(input_path, beam_size=5,vad_filter=True)
    
    transcript = []
    for segment in segments:
        transcript.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })

    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(transcript, f, indent=2, ensure_ascii=False)

    print(f"Transcript saved to {output_path}")
    return transcript


def get_file_name(path):
    file_name = os.path.basename(path)
    return file_name


def get_duration(path):
    probe = ffmpeg.probe(path)
    duration = float(probe["format"]["duration"])
    return duration


if __name__ == "__main__":
    
    path = "backend/search_and_index/test.mp4"
    start = time.time()

    audio_path = extract_audio(path)
    file_name = get_file_name(path)
    duration = get_duration(path)


    if audio_path:
        transcript = transcribe_audio(audio_path)
        summary_text = summary_generator(transcript)

        connection = sqlite3.connect("brain.db")
        initialize_db()

        # Check if file path already exists
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (path,))
        result = cursor.fetchone()

        if result:
            media_id = result[0]
            print(f"File already exists in DB with media_id: {media_id}")
        else:
            media_id = save_to_db(path, file_name, duration, transcript, summary=summary_text)
            if media_id is None:
                print("Failed to save to database")
                connection.close()
                exit(1)

        connection.close()

        save_to_vector_db(media_id, file_name, path, transcript, summary=summary_text)
        save_summary_vector(media_id, file_name, summary_text)
        
        
        
 



    end = time.time()

    print("Execution time:",end-start)
