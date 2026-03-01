import sqlite3
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/query")
def query():
    try:
        with sqlite3.connect("backend.db") as conn:
            pass
    except sqlite3.OperationalError as e:
        print("Failed to open database:", e)
