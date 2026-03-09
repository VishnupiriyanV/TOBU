import cv2
from PIL import Image
import os
from semantic_engine import VECTOR_DB_PATH
from sentence_transformers import SentenceTransformer, util
import lancedb
import json
import torch
from model_downloader import MODEL_VISUAL_PATH

INTERVAL_SECONDS =2 #frame extraction 
BATCH_SIZE = 50 #50 frames cap for storing before saving in the DB
THUMBNAIL_PATH = os.path.join("data", "thumbnails")
THUMBNAIL_MAX_SIZE= (320,320)
THUMBNAIL_QUALITY = 80


device = "cuda" if torch.cuda.is_available() else "cpu"
visual_model = SentenceTransformer(MODEL_VISUAL_PATH, device=device,model_kwargs={"local_files_only":True})

def index_video_visually(video_path, media_id, db_path=VECTOR_DB_PATH):

    if not os.path.exists(THUMBNAIL_PATH):
        os.makedirs(THUMBNAIL_PATH)

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    interval = int(fps*INTERVAL_SECONDS) #extract one frame per second

    frames_batch = []
    count =0
    batch_size = BATCH_SIZE

    db = lancedb.connect(VECTOR_DB_PATH)
    table_name = "visual_moments"

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
            thumb_path = THUMBNAIL_PATH
            full_thumb_path = os.path.join(THUMBNAIL_PATH, thumb_filename)
            pil_img.thumbnail(THUMBNAIL_MAX_SIZE)
            pil_img.save(full_thumb_path,"jpeg",quality=THUMBNAIL_QUALITY )

            #placeholder for model embedding
            
            img_embedding = visual_model.encode(pil_img)






            frames_batch.append({
                "vector": img_embedding,
                "timestamp": timestamp,
                "media_id": media_id,
                "thumbnail_path" : full_thumb_path

            })

            # after batch size save database
            if len(frames_batch) >= batch_size:
                
                _upsert_lancedb(db, table_name, frames_batch)
                frames_batch = []

        count += 1

    if frames_batch:
        _upsert_lancedb(db, table_name, frames_batch)

    cap.release()
    print(f"Visual indexing : {media_id}")

def _upsert_lancedb(db, table_name, data):
    try:
        table = db.open_table(table_name)
        table.add(data)
    except Exception:
        db.create_table(table_name, data=data)



    

    


        



def search_visual_moments(query_text, db_path=VECTOR_DB_PATH, limit=5):

    db = lancedb.connect(db_path)
    table_name = "visual_moments"

    try:
        table = db.open_table(table_name)
    except Exception as e:
        return json.dumps({"error": "Table not found", "details": str(e)}, indent=2)


    query_vector = visual_model.encode(query_text).tolist()


    results = table.search(query_vector).limit(limit).to_list()


    for res in results:
        if "vector" in res:
            del res["vector"] 
        
        res["media_id"] = str(res["media_id"])

    
    return json.dumps(results, indent=2, ensure_ascii=False)



            
            

            



    
