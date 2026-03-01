import sqlite3
import pandas as pd 


connection = sqlite3.connect("brain.db")

#create table

mediaFiles_create_table = """

CREATE TABLE IF NOT EXISTS media_files (
id INTEGER PRIMARY KEY AUTOINCREMENT,
file_path TEXT UNIQUE NOT NULL,
file_name TEXT UNIQUE NOT NULL,
duration_seconds REAL,
added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
status TEXT DEFAULT 'pending' --pending,processing,indexed,error


)

"""


transcript_fts ="""

CREATE VIRTUAL TABLE transcripts_fts USING fts5(
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
    cursor.execute("DROP TABLE IF EXISTS transcripts_fts")
    connection.commit()
except Exception as e:
    print(f"drop error: {e}")
    connection.rollback()

try:
    cursor.execute(transcript_fts)
    connection.commit()
except Exception as e:
    print(f"transcripts_fts error: {e}")
    connection.rollback()



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





