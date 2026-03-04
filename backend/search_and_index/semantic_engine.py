
from sentence_transformers import SentenceTransformer
import lancedb
import json
import pandas as pd


MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

#converts text to embedding
def embed(sentences):
    
    embeddings = MODEL.encode(sentences)

    if len(embeddings.shape) == 1:
        return embeddings.tolist()

    return embeddings.tolist()
    


def sentence_window(data,window_size=3):
    final_list=[]
    chunks = [seg["text"] for seg in data]
    n=len(chunks)
    
    
    for text in range(1,n):
        starting_index=max(0,text-(window_size//2))
        ending_index=min(n,text+(window_size//2)+1) 
        window_list=chunks[starting_index:ending_index]
        final_list.append(window_list)

    return final_list
def save_to_vector_db(media_id,file_name,file_path,transcript_data,db_path="vector_data"):
    
    windowed_text_lists = sentence_window(transcript_data)

    texts_to_embed = [" ".join(window) for window in windowed_text_lists]

    #generate the embedding
    
    embeddings = embed(texts_to_embed)

    

    #map data

    data = []
    for i in range(len(windowed_text_lists)):
        data.append({
            "vector" : embeddings[i],
            "text" : transcript_data[i]["text"],
            "context": texts_to_embed[i],
            "start" : transcript_data[i]["start"],
            "file_name": file_name,
            "file_path":file_path,
            "media_id" : media_id

        })

    # storing the data in lancedb

    db = lancedb.connect(db_path)
    table_name = "semantic_segments"

    if table_name in db.table_names():
        table = db.open_table(table_name)
        table.add(data)
    else:
        db.create_table(table_name,data=data)


def semantic_search(query,limit,db_path="vector_data"):
    db = lancedb.connect(db_path)
    table = db.open_table("semantic_segments")
    
    
    query_vector = embed([query])[0]
        
    results = table.search(query_vector).limit(limit).to_pandas()

    columns_to_keep = ["file_name", "file_path", "start", "text", "_distance"]
    df = df[columns_to_keep]
    

    json_output = df.to_json(orient="records", indent=4)
    
    return json_output

    



    





