import sqlite3
import pandas as pd 


connection = sqlite3.connect("brain.db")

#create table

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


cursor = connection.cursor()



try:
    cursor.execute(mediaFiles_create_table)
    connection.commit()
except Exception as e:
    print(e)
    connection.rollback()


