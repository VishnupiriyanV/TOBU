
#to pre-download the models

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VISUAL_MODEL = "clip-ViT-B-32"
SUMMARIZER_MODEL = "sshleifer/distilbart-cnn-6-6"
WHISPER_MODEL = "distil-large-v3"


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_VISUAL_PATH = os.path.join(MODEL_DIR, "clip-ViT-B-32")
MODEL_SEMANTIC_PATH = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2")
MODEL_SUMMARIZER_PATH = os.path.join(MODEL_DIR, "distilbart-cnn-6-6")
MODEL_WHISPER_PATH = os.path.join(MODEL_DIR, "whisper-distil-large-v3")

def ensure_semantic_model():
    if not os.path.exists(MODEL_SEMANTIC_PATH):
        model_semantic = SentenceTransformer(SEMANTIC_MODEL)
        model_semantic.save(MODEL_SEMANTIC_PATH)


def ensure_visual_model():
    if not os.path.exists(MODEL_VISUAL_PATH):
        model_visual = SentenceTransformer(VISUAL_MODEL)
        model_visual.save(MODEL_VISUAL_PATH)


def ensure_summarizer_model():
    if not os.path.exists(MODEL_SUMMARIZER_PATH):
        tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZER_MODEL)
        tokenizer.save_pretrained(MODEL_SUMMARIZER_PATH)
        model.save_pretrained(MODEL_SUMMARIZER_PATH)


def ensure_whisper_model():
    if not os.path.exists(MODEL_WHISPER_PATH):
        from faster_whisper import download_model
        download_model(WHISPER_MODEL, output_dir=MODEL_WHISPER_PATH)


def ensure_all_models():
    ensure_semantic_model()
    ensure_visual_model()
    ensure_summarizer_model()
    ensure_whisper_model()


if __name__ == "__main__":
    ensure_all_models()
    print("All local models are ready.")