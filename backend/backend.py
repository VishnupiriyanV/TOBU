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
    print(str(item))
    return item

    
    # try:
    #     create_table = "CREATE TABLE IF NOT EXISTS queries (date TEXT PRIMARY KEY, query TEXT NOT NULL);"
    #     now = datetime.datetime.now()
    #     insert_values = "INSERT INTO artists (date,query) VALUES(" + str(now) + ");"

    #     # Creating table and inserting the date and query into it
    #     with sqlite3.connect("backend.db") as conn:
    #         cursor = conn.cursor()
    #         cursor.execute(create_table)
    #         conn.commit()
    # except sqlite3.OperationalError as e:
    #     print(e)

