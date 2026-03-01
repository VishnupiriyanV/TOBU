import ffmpeg
import json
import warnings
from faster_whisper import WhisperModel #needs cuda_12 toolkit for gpu
import time
import os
from database import save_to_db
import sqlite3



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
    
    path = "test.mp4"
    start = time.time()

    audio_path = extract_audio(path)
    file_name = get_file_name(path)
    duration = get_duration(path)

    if audio_path:
        transcript = transcribe_audio(audio_path)

        connection = sqlite3.connect("brain.db")

        save_to_db(path,file_name,duration,transcript)
        connection.close()




    end = time.time()

    print("Execution time:",end-start)
