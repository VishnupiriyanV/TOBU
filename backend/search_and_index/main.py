from aural_engine import extract_audio,get_duration,get_file_name,transcribe_audio
from sql_database import save_to_db, search_to_json, initialize_db,DATABASE_PATH
from semantic_engine import save_to_vector_db, save_summary_vector
import sqlite3
from summarizer import summary_generator
from visual_engine import index_video_visually
import warnings
import time
import os

warnings.filterwarnings("ignore")





if __name__ == "__main__":

    path = "C:/Helm/FossHack/TOBU/test3.mp4"
    start = time.time()

    audio_path = extract_audio(path)
    file_name = get_file_name(path)
    duration = get_duration(path)


    if audio_path:
        transcript = transcribe_audio(audio_path)
        os.remove(audio_path)
        summary_text = summary_generator(transcript)

        connection = sqlite3.connect(DATABASE_PATH)
        initialize_db()

        
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (path,))
        result = cursor.fetchone()

        if result:
            media_id = result[0]
            print(f"File already exists in DB with media_id: {media_id}")
        else:
            media_id = save_to_db(path, file_name, duration, transcript, summary=summary_text)
            if media_id is None:
                print("Failed to save to database")
                connection.close()
                exit(1)

        connection.close()

        save_to_vector_db(media_id, file_name, path, transcript, summary=summary_text)
        save_summary_vector(media_id, file_name, summary_text)
    
        print("visual indexing starts:")
        index_video_visually(path, media_id)
        
        
 



    end = time.time()

    print("Execution time:",end-start)