import sqlite3
from fastapi import FastAPI
import datetime
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

class Item(BaseModel):
    query: str

app = FastAPI()

# CORS Stuff
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.post("/query")
def query(item: Item):
    query_string = str(item)
    query = query_string.strip("query=")
    try:
        create_table = "CREATE TABLE IF NOT EXISTS queries (date TEXT PRIMARY KEY, query TEXT NOT NULL);"
        now = datetime.datetime.now()
        date = str(now)
        insert_values = "INSERT INTO queries (date,query) VALUES(" + "'" + date + "'" + "," + query + ");"
        # Creating table and inserting the date and query into it
        with sqlite3.connect("backend.db") as conn:
            cursor = conn.cursor()
            cursor.execute(create_table)
            cursor.execute(insert_values)
            conn.commit()
    except sqlite3.OperationalError as e:
        print("Sqlite error:", e)

