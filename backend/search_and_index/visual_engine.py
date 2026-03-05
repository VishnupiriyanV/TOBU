import cv2
from PIL import Image
import os
from semantic_engine import VECTOR_DB_PATH
import lancedb


INTERVAL_SECONDS =2 #frame extraction 
BATCH_SIZE = 50 #50 frames cap for storing before saving in the DB
THUMBNAIL_PATH = os.path.join("backend", "search_and_index", "tempfile", "thumbnails")
THUMBNAIL_MAX_SIZE= (320,320)
THUMBNAIL_QUALITY = 80


def  index_video_visually(video_path,media_id,db_path=VECTOR_DB_PATH,):

    if not os.path.exists(THUMBNAIL_PATH):
        os.makedirs(THUMBNAIL_PATH)

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    interval = int(fps*) #extract one frame per second

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

            pil_img.thumnail(THUMBNAIL_MAX_SIZE)
            pil_img.save(thumb_path,"jpeg",quality=THUMBNAIL_QUALITY )

            #placeholder for model embedding






            frames_batch.append({
                "vector": img_embedding, #change after adding model
                "timestamp": timestamp,
                "media_id": media_id,
                "thumbnail_path" : thumb_path

            })

            # after batch size save database
            if len(frames_batch)>= batch_size:
                if table_name in db.table_names():
                    db.open_table(table_name).add(frames_batch)
                else:
                    db.create_table(table_name,data=frames_batch)
                frames_batch = [] 

        count += 1

        
    if frames_batch:
        if table_name in db.table_names():
            db.open_table(table_name).add(frames_batch)
        else:
            db.create_table(table_name, data=frames_batch)

    cap.release() 
    print(f"Visual indexing  for media_id: {media_id}")


        








            
            

            



    
