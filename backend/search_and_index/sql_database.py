import sqlite3
import json
import os

DB_DIR = os.path.join("data","database")
DATABASE_PATH = os.path.join(DB_DIR, "brain.db")
os.makedirs(DB_DIR, exist_ok=True)

#create table

def initialize_db():
    with sqlite3.connect(DATABASE_PATH) as connection:
        mediaFiles_create_table = """

        CREATE TABLE IF NOT EXISTS media_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        source_type TEXT DEFAULT 'video',  --'video','pdf','markdown','txt'
        duration_seconds REAL, -- NULL for non media
        summary TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending' --pending,processing,indexed,error


        )

        """


        transcript_fts ="""

        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts USING fts5(
            media_id UNINDEXED ,
            location_start UNINDEXED,
            location_end UNINDEXED,
            content,
            file_name
            );
        """


        cursor = connection.cursor()



        try:
            cursor.execute(mediaFiles_create_table)
        except Exception as e:
            print(f"media_files error: {e}")
            connection.rollback()

        




        try:
            cursor.execute(transcript_fts)
            connection.commit()
        except Exception as e:
            print(f"transcripts_fts error: {e}")
            connection.rollback()

#initialize_db()

def get_media_id(file_path):
    """Get media_id for an existing file path."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        return result[0] if result else None


#FOR SAVING TRANSCRIPT
def save_to_db(file_path, file_name, duration, transcript_data,source_type="video", summary=None):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    try:
        insert_cmd = """INSERT INTO media_files (file_path,file_name,duration_seconds,source_type,status,summary) VALUES (?,?,?,?,'indexed',?)"""
        cursor.execute(insert_cmd, (file_path, file_name, duration,source_type, summary))

        media_id = cursor.lastrowid

        data_to_insert = [
            (media_id, seg.get('start') or seg.get('page'), seg.get('end') or seg.get('page'), seg['text'], file_name)
            for seg in transcript_data
        ]

        cursor.executemany("""
            INSERT INTO transcripts_fts (media_id, location_start, location_end, content, file_name)
            VALUES (?, ?, ?, ?, ?)
        """, data_to_insert)

        connection.commit()
        print(f"indexed: {file_name}")

        return media_id

    except Exception as e:
        print(f"Database Error:{e}")
        connection.rollback()
        return None

    finally:
        connection.close()


#for final json

def search_to_json(query, output_file="search_results.json"):
    with sqlite3.connect(DATABASE_PATH) as connection:
        
        connection.row_factory = sqlite3.Row 
        cursor = connection.cursor()
        
        search_query = """
            SELECT 
                f.file_name, 
                f.file_path, 
                t.location_start, 
                t.location_end, 
                t.content as text,
                t.rank as score
            FROM transcripts_fts t
            JOIN media_files f ON t.media_id = f.id
            WHERE t.content MATCH ? 
            ORDER BY rank 
            LIMIT 50
        """
        
        query1 = f'"{query}"'
        cursor.execute(search_query, (query1,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "file-name": row["file_name"],
                "file-path": os.path.abspath(row["file_path"]), 
                "start": row["location_start"],
                "end": row["location_end"],
                "text": row["text"],
                "score": row["score"]
                })
        

        return results
            


def save_doc_to_db(file_path, file_name, segments, source_type="note", summary=None):
    return save_to_db(file_path, file_name, duration=None, transcript_data=segments, source_type=source_type, summary=summary)

