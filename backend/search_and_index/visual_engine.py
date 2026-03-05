import cv2
from PIL import Image
import os
from semantic_engine import VECTOR_DB_PATH

THUMBNAIL_PATH = os.path.join("backend", "search_and_index", "tempfile", "thumbnails")

def  index_video_visually(video_path,media_id,db_path=VECTOR_DB_PATH,):

    if not os.path.exists(THUMBNAIL_PATH):
        os.makedirs(THUMBNAIL_PATH)

    
