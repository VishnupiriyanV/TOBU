import ffmpeg
import json
import warnings
from faster_whisper import WhisperModel
import time

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
    model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")

    segments, info = model.transcribe(input_path, beam_size=5)

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




if __name__ == "__main__":
    
    path = "test.mp4"
    start = time.time()

    audio_path = extract_audio(path)

    if audio_path:
        transcribe_audio(audio_path)
    end = time.time()

    print("Exceution time:",end-start)
