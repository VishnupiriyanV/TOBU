import ffmpeg
import json
from faster_whisper import WhisperModel #needs cuda_12 toolkit for gpu
import os
import uuid
import torch


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
TEMP_DIR = os.path.join(PROJECT_ROOT, "data", "temp")


if __package__:
    from backend.search_and_index.model_downloader import MODEL_WHISPER_PATH
else:
    from model_downloader import MODEL_WHISPER_PATH

if torch.cuda.is_available():
    device = "cuda"
    compute = "int8"
else:
    device = "cpu"
    compute = "int8"

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        if not os.path.exists(MODEL_WHISPER_PATH):
            raise RuntimeError(f"Whisper model not found at {MODEL_WHISPER_PATH}. Please run onboarding.")
        _whisper_model = WhisperModel(MODEL_WHISPER_PATH, device=device, compute_type=compute, local_files_only=True)
    return _whisper_model



def extract_audio(input_path, output_path=None):
    """converts to 16kHz mono WAV."""

    if output_path is None:
        output_path = os.path.join(TEMP_DIR, f"temp_{uuid.uuid4().hex}.wav")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return output_path
    except ffmpeg.Error as e:
        stderr_output = e.stderr.decode('utf-8') if e.stderr else "Unknown error"
        print(f"Error extracting audio: {stderr_output}")
        print(f"Input file exists: {os.path.exists(input_path)}")
        return None


def transcribe_audio(input_path, output_path=None):
    if output_path is None:
        output_path = os.path.join(TEMP_DIR, f"transcript_{uuid.uuid4().hex}.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    

    segments, info = get_whisper_model().transcribe(input_path, beam_size=5,vad_filter=True)
    
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
