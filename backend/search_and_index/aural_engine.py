import ffmpeg
import json
import os
import uuid
import torch
import sys
from faster_whisper import WhisperModel

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.expanduser("~/.tobu")
    os.makedirs(PROJECT_ROOT, exist_ok=True)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))

TEMP_DIR = os.path.join(PROJECT_ROOT, "data", "temp")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_WHISPER_PATH = os.path.join(MODEL_DIR, "whisper-distil-large-v3")

# Lazy load model
_WHISPER_MODEL = None

def get_whisper():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        if torch.cuda.is_available():
            device = "cuda"
            compute = "int8"
        else:
            device = "cpu"
            compute = "int8"
        
        # Check if local model exists
        if os.path.exists(MODEL_WHISPER_PATH):
            model_to_load = MODEL_WHISPER_PATH
            print(f"Loading local Whisper model from {MODEL_WHISPER_PATH}...")
        else:
            model_to_load = "distil-large-v3"
            print(f"Loading Whisper model {model_to_load} (may download if not cached)...")

        try:
            _WHISPER_MODEL = WhisperModel(model_to_load, device=device, compute_type=compute)
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            # Fallback to CPU if CUDA fails
            if device == "cuda":
                print("Falling back to CPU...")
                _WHISPER_MODEL = WhisperModel(model_to_load, device="cpu", compute_type="int8")
            else:
                raise e
    return _WHISPER_MODEL



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
    
    model = get_whisper()
    segments, info = model.transcribe(input_path, beam_size=5, vad_filter=True)
    
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
    return os.path.basename(path)


def get_duration(path):
    probe = ffmpeg.probe(path)
    return float(probe["format"]["duration"])

