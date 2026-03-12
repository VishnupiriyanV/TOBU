import sqlite3
import json
import os
import hashlib

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
        status TEXT DEFAULT 'pending', --pending,processing,indexed,error
        file_hash TEXT


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
            cursor.execute(transcript_fts)
            connection.commit()
        except Exception as e:
            print(f"Database init error: {e}")
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
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        existing_row = cursor.fetchone()
        if existing_row is not None:
            existing_media_id = existing_row[0]
            cursor.execute("DELETE FROM transcripts_fts WHERE media_id = ?", (existing_media_id,))
            cursor.execute("DELETE FROM media_files WHERE id = ?", (existing_media_id,))
        current_hash = compute_file_hash(file_path)
        insert_cmd = """INSERT INTO media_files (file_path,file_name,duration_seconds,source_type,status,summary,file_hash) VALUES (?,?,?,?,'indexed',?,?)"""
        cursor.execute(insert_cmd, (file_path, file_name, duration,source_type, summary,current_hash))

        media_id = cursor.lastrowid

        data_to_insert = [
            (media_id,
             seg['start'] if seg.get('start') is not None else seg.get('page'),
             seg['end'] if seg.get('end') is not None else seg.get('page'),
             seg['text'], file_name)
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
    
def compute_file_hash(path,chunk_size=8192): #8kb
    h = hashlib.sha256()
    with open(path,"rb") as f:
        chunk = f.read(chunk_size)
        while chunk:
            h.update(chunk)
            chunk = f.read(chunk_size)
    return h.hexdigest()


#return true if the file should be processed (not yet indexed, or hash has changed)
def should_process(file_path):
    if not os.path.exists(file_path):
        return False
        
    current_hash = compute_file_hash(file_path)
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT file_hash FROM media_files WHERE file_path = ?", (file_path,)
        ).fetchone()

    if row is None:
        return True 
    return row[0] != current_hash

def delete_file_records(file_path):
    """Remove a file's records from media_files and transcripts_fts."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        if row is None:
            return
        media_id = row[0]
        cursor.execute("DELETE FROM transcripts_fts WHERE media_id = ?", (media_id,))
        cursor.execute("DELETE FROM media_files WHERE id = ?", (media_id,))
        connection.commit()
        print(f"Removed from index: {file_path}")


def save_doc_to_db(file_path, file_name, segments, source_type="note", summary=None):
    return save_to_db(file_path, file_name, None, segments, source_type=source_type, summary=summary)