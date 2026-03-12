
from sentence_transformers import SentenceTransformer
import lancedb
import json
import pandas as pd
import os
from model_downloader import MODEL_SEMANTIC_PATH

VECTOR_DB_PATH = os.path.join("data", "database", "vector_data")

# Load model in offline mode
MODEL = SentenceTransformer(
    MODEL_SEMANTIC_PATH,
    model_kwargs={"local_files_only": True}
)


#converts text to embedding
def embed(sentences):
    
    embeddings = MODEL.encode(sentences)
    return embeddings.tolist()
    


def sentence_window(data,window_size=3):
    final_list=[]
    chunks = [seg["text"] for seg in data]
    n=len(chunks)
    
    
    for text in range(0,n):
        starting_index=max(0,text-(window_size//2))
        ending_index=min(n,text+(window_size//2)+1) 
        window_list=chunks[starting_index:ending_index]
        final_list.append(window_list)

    return final_list
def save_to_vector_db(media_id, file_name, file_path, transcript_data, summary=None, db_path=VECTOR_DB_PATH):

    
    
    windowed_text_lists = sentence_window(transcript_data)

    texts_to_embed = [" ".join(window) for window in windowed_text_lists]

    #generate the embedding
    
    embeddings = embed(texts_to_embed)

    

    #map data

    data = []
    for i in range(len(windowed_text_lists)):
        location_start = transcript_data[i].get("start") or transcript_data[i].get("page")
        location_end = transcript_data[i].get("end") or transcript_data[i].get("page")

        data.append({
            "vector" : embeddings[i],
            "text" : transcript_data[i]["text"],
            "context": texts_to_embed[i],
            "start" : location_start,
            "end":location_end,
            "file_name": file_name,
            "file_path":file_path,
            "media_id" : media_id

        })

    if not data:
        print(f" No valid segments:{file_name}")
        return
    
    # storing the data in lancedb

    db = lancedb.connect(db_path)
    table_name = "semantic_segments"

    if table_name in db.table_names():
        table = db.open_table(table_name)
        table.add(data)
    else:
        db.create_table(table_name,data=data)


def semantic_search(query, limit, db_path=VECTOR_DB_PATH):
    db = lancedb.connect(db_path)
    table = db.open_table("semantic_segments")

    query_vector = embed([query])[0]

    results = table.search(query_vector).limit(limit).to_pandas()

    formatted_results = []
    for _, r in results.iterrows():
        formatted_results.append({
            "file-name": r["file_name"],
            "file-path": r["file_path"],
            "start": r["start"],
            "end": r.get("end", r["start"]), 
            "text": r["text"],
            "score": r["_distance"] 
        })
        
    return formatted_results

    
def save_summary_vector(media_id,file_name,summary,db_path = VECTOR_DB_PATH):
    db = lancedb.connect(db_path)
    table_name = "summary_segments"

    embedding = embed([summary])[0]

    data = [{
        "vector": embedding,
        "summary": summary,
        "file_name": file_name,
        "media_id": media_id
    }]

    if table_name in db.table_names():
        table = db.open_table(table_name)
        table.add(data)
    else:
        db.create_table(table_name, data=data)

def file_search(query,limit=5,db_path=VECTOR_DB_PATH):
    db = lancedb.connect(db_path)
    table = db.open_table("summary_segments")
    
    query_vector = embed([query])[0]

    results = table.search(query_vector).limit(limit).to_pandas()

    records = results.to_dict(orient="records")
    for r in records:
        r.pop("vector", None)
    return records

    





