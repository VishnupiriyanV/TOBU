import cv2
from PIL import Image
import os
from sentence_transformers import SentenceTransformer, util
import lancedb
import json
import torch

if __package__:
    from backend.search_and_index.semantic_engine import VECTOR_DB_PATH
    from backend.search_and_index.model_downloader import MODEL_VISUAL_PATH
else:
    from semantic_engine import VECTOR_DB_PATH
    from model_downloader import MODEL_VISUAL_PATH

INTERVAL_SECONDS = 2  # extract one frame every  seconds
BATCH_SIZE = 50 #50 frames cap for storing before saving in the DB
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
THUMBNAIL_PATH = os.path.join(PROJECT_ROOT, "data", "thumbnails")
THUMBNAIL_MAX_SIZE= (320,320)
THUMBNAIL_QUALITY = 80


device = "cuda" if torch.cuda.is_available() else "cpu"
_visual_model = None

def get_visual_model():
    global _visual_model
    if _visual_model is None:
        if not os.path.exists(MODEL_VISUAL_PATH):
            raise RuntimeError(f"Visual model not found at {MODEL_VISUAL_PATH}. Please run onboarding.")
        _visual_model = SentenceTransformer(MODEL_VISUAL_PATH, device=device, model_kwargs={"local_files_only": True})
    return _visual_model


def clear_visual_for_media(media_id, db_path=VECTOR_DB_PATH):
    db = lancedb.connect(db_path)
    table_name = "visual_moments"

    if table_name in db.table_names():
        table = db.open_table(table_name)
        table.delete(f"media_id = {int(media_id)}")

    if os.path.isdir(THUMBNAIL_PATH):
        prefix = f"{media_id}_"
        for name in os.listdir(THUMBNAIL_PATH):
            if name.startswith(prefix):
                file_path = os.path.join(THUMBNAIL_PATH, name)
                try:
                    os.remove(file_path)
                except Exception:
                    pass

def index_video_visually(video_path, media_id, db_path=VECTOR_DB_PATH):

    if not os.path.exists(THUMBNAIL_PATH):
        os.makedirs(THUMBNAIL_PATH)

    clear_visual_for_media(media_id, db_path)

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        print(f"Invalid FPS for video: {video_path}")
        cap.release()
        return

    interval = int(fps * INTERVAL_SECONDS)

    frames_batch = []
    count =0
    batch_size = BATCH_SIZE

    db = lancedb.connect(VECTOR_DB_PATH)
    table_name = "visual_moments"

    if table_name in db.table_names():
        table = db.open_table(table_name)
    else:
        table = None

    while cap.isOpened():
        ret,frame = cap.read()

        if not ret:
            
            break

        if count % interval == 0:

            #converts BGR to RGB since ai models and pil use rgb

            colour_converted = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(colour_converted)

            timestamp = round(count/fps,2)
            thumb_filename = f"{media_id}_{timestamp}.jpg"
            
            full_thumb_path = os.path.join(THUMBNAIL_PATH, thumb_filename)
            pil_img.thumbnail(THUMBNAIL_MAX_SIZE)
            pil_img.save(full_thumb_path,"jpeg",quality=THUMBNAIL_QUALITY )

            
            
            img_embedding = get_visual_model().encode(pil_img).tolist()






            frames_batch.append({
                "vector": img_embedding,
                "timestamp": timestamp,
                "media_id": media_id,
                "thumbnail_path" : full_thumb_path

            })

            # after batch size save database
            if len(frames_batch) >= batch_size:
                if table is None:
                    table = db.create_table(table_name, data=frames_batch)
                else:
                    table.add(frames_batch)
                frames_batch = []

        count += 1

    if frames_batch:
        if table is None:
            table = db.create_table(table_name, data=frames_batch)
        else:
            table.add(frames_batch)

    cap.release()
    print(f"Visual indexing : {media_id}")



# /?query=image.png&image_path=true
def search_visual_moments(query,image_path = False, db_path=VECTOR_DB_PATH, limit=5):

    db = lancedb.connect(db_path)
    table_name = "visual_moments"

    try:
        table = db.open_table(table_name)
    except Exception:
        return []
    
    if image_path:
        img = cv2.imread(query)
        colour_converted = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(colour_converted)
        query_vector = get_visual_model().encode(pil_img).tolist()
    else:
        query_vector = get_visual_model().encode(query).tolist()


    results = table.search(query_vector).limit(limit).to_list()


    for res in results:
        if "vector" in res:
            del res["vector"] 
        
        res["media_id"] = str(res["media_id"])

    
    return results

            
            

            



    
