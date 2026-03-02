import sqlite3
import json
import os

DATABASE_PATH = "brain.db"

#create table

def initialize_db():

    with sqlite3.connect(DATABASE_PATH) as connection:
        mediaFiles_create_table = """

        CREATE TABLE IF NOT EXISTS media_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        duration_seconds REAL,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending' --pending,processing,indexed,error


        )

        """


        transcript_fts ="""

        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts USING fts5(
            media_id UNINDEXED ,
            start_time UNINDEXED,
            end_time UNINDEXED,
            content,
            file_name
            );
        """


        cursor = connection.cursor()



        try:
            cursor.execute(mediaFiles_create_table)
            connection.commit()
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

#FOR SAVING TRANSCRIPT
def save_to_db(file_path,file_name,duration,transcript_data):
    connection = sqlite3.connect("brain.db")
    cursor = connection.cursor()

    try:

        insert_cmd = """INSERT INTO media_files (file_path,file_name,duration_seconds,status) VALUES (?,?,?,'indexed')"""
        cursor.execute(insert_cmd,(file_path,file_name,duration,))

        media_id = cursor.lastrowid

        data_to_insert = [
            (media_id, seg['start'], seg['end'], seg['text'], file_name) 
            for seg in transcript_data
        ]
        
        cursor.executemany("""
            INSERT INTO transcripts_fts (media_id, start_time, end_time, content, file_name)
            VALUES (?, ?, ?, ?, ?)
        """, data_to_insert)

        connection.commit()
        print(f"indexed: {file_name}")

    except Exception as e:
        print(f"Database Error:{e}")
        connection.rollback()

    connection.close()


#for final json

def search_to_json(query, output_file="search_results.json"):
    with sqlite3.connect("brain.db") as connection:
        
        connection.row_factory = sqlite3.Row 
        cursor = connection.cursor()
        
        search_query = """
            SELECT 
                f.file_name, 
                f.file_path, 
                t.start_time, 
                t.end_time, 
                t.content as text
            FROM transcripts_fts t
            JOIN media_files f ON t.media_id = f.id
            WHERE t.content MATCH ? 
            ORDER BY rank 
            LIMIT 50
        """
        

        cursor.execute(search_query, (query,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "file-name": row["file_name"],
                "file-path": os.path.abspath(row["file_path"]), 
                "start": row["start_time"],
                "end": row["end_time"],
                "text": row["text"]
                })
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            




