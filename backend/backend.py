import sqlite3
from fastapi import FastAPI
import datetime

app = FastAPI()

@app.post("/query")
def query():
    try:
        create_table = "CREATE TABLE IF NOT EXISTS queries (date TEXT PRIMARY KEY, query TEXT NOT NULL);"
        now = datetime.datetime.now()
        insert_values = "INSERT INTO artists (date,query) VALUES('Bud Powell');"

        # Creating table and inserting the date and query into it
        with sqlite3.connect("backend.db") as conn:
            cursor = conn.cursor()
            cursor.execute(create_table)
            conn.commit()
    except sqlite3.OperationalError as e:
        print(e)

