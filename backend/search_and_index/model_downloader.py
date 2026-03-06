
#to pre-download the models

from sentence_transformers import SentenceTransformer
from faster_whisper import WhisperModel
import os

SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VISUAL_MODEL = "clip-ViT-B-32"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_VISUAL_PATH = os.path.join(MODEL_DIR, "clip-ViT-B-32")
MODEL_SEMANTIC_PATH = os.path.join(MODEL_DIR, "all-MiniLM-L6-v2")

if not os.path.exists(MODEL_SEMANTIC_PATH):
    model_semantic = SentenceTransformer(SEMANTIC_MODEL)
    model_semantic.save(MODEL_SEMANTIC_PATH)
else:
    print(f"Semantic model already exists at: {MODEL_SEMANTIC_PATH}")

if not os.path.exists(MODEL_VISUAL_PATH):
    model_visual = SentenceTransformer(VISUAL_MODEL)
    model_visual.save(MODEL_VISUAL_PATH)
else:
    print(f"Visual model already exists at: {MODEL_VISUAL_PATH}")

