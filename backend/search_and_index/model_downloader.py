
#to pre-download the models

from sentence_transformers import SentenceTransformer
from faster_whisper import WhisperModel
import os

SEMANTIC_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VISUAL_MODEL = "clip-ViT-B-32"

MODEL_VISUAL_PATH = os.path.join("backend","models","clip-ViT-B-32")
MODEL_SEMANTIC_PATH = os.path.join("backend","models","all-MiniLM-L6-v2")

model_dir = os.path.join("backend", "search_and_index", "models")
os.makedirs(model_dir, exist_ok=True)

model_semantic = SentenceTransformer(SEMANTIC_MODEL)
model_semantic.save(MODEL_SEMANTIC_PATH)

model_visual = SentenceTransformer(VISUAL_MODEL)
model_visual.save(MODEL_VISUAL_PATH)

