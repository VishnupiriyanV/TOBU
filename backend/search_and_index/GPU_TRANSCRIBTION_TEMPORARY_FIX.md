If you want to use GPU for transcribing in faster-whisper ,

then change "cpu" to "cuda" in the aural_engine.py 

after running it you might run into this runtime error:

"RuntimeError: Library cublas64_12.dll is not found or cannot be loaded"

to fix this install these to libs: (make sure it is in venv)

pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

and if the issues still persists, then copy the dll files from these paths

.venv\Lib\site-packages\nvidia\cublas\bin
.venv\Lib\site-packages\nvidia\cudnn\bin

and paste it in 

.venv\Lib\site-packages\ctranslate2

it should solve the issue for now 
but need to find something different for the final version though



import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer

# 1. Load the lightweight, MIT-licensed embedding model
# all-MiniLM-L6-v2 is ~80MB and very fast on CPUs
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_sliding_window_chunks(segments, window_size=3):
    """
    Creates overlapping chunks of text for better context.
    If window_size=3, it takes [Current-1, Current, Current+1].
    """
    chunks = []
    num_segments = len(segments)
    
    for i in range(num_segments):
        # Determine the start and end of the window
        start_idx = max(0, i - (window_size // 2))
        end_idx = min(num_segments, i + (window_size // 2) + 1)
        
        # Join the text within the window
        window_text = " ".join([segments[j]['text'] for j in range(start_idx, end_idx)])
        
        chunks.append({
            "text": window_text,
            "start": segments[i]['start'], # Anchor to the actual start time
            "original_text": segments[i]['text'] # Keep the specific line
        })
    return chunks

def save_to_vector_db(media_id, file_name, file_path, segments, db_path="vector_data"):
    """
    Chunks transcript, embeds it, and saves it to LanceDB.
    """
    # Create sliding window chunks
    chunks = get_sliding_window_chunks(segments, window_size=3)
    
    # Generate embeddings for the windowed text
    texts_to_embed = [c['text'] for c in chunks]
    embeddings = model.encode(texts_to_embed).tolist()
    
    # Prepare data for LanceDB
    data = []
    for i, chunk in enumerate(chunks):
        data.append({
            "vector": embeddings[i],
            "text": chunk['original_text'], # Display the specific line
            "context": chunk['text'],       # But search based on context
            "start": chunk['start'],
            "file_name": file_name,
            "file_path": file_path,
            "media_id": media_id
        })
    
    # Connect and Save
    db = lancedb.connect(db_path)
    table_name = "semantic_segments"
    
    if table_name in db.table_names():
        table = db.open_table(table_name)
        table.add(data)
    else:
        db.create_table(table_name, data=data)
    
    print(f"✅ Semantic index created for: {file_name}")

def semantic_search(query, limit=10, db_path="vector_data"):
    """
    Searches by meaning, not just keywords.
    """
    db = lancedb.connect(db_path)
    table = db.open_table("semantic_segments")
    
    # Encode user query
    query_vector = model.encode(query).tolist()
    
    # Search LanceDB
    results = table.search(query_vector).limit(limit).to_list()
    
    # Format to match your JSON structure
    formatted_results = []
    for r in results:
        formatted_results.append({
            "file-name": r["file_name"],
            "file-path": r["file_path"],
            "start": r["start"],
            "text": r["text"],
            "score": r["_distance"] # Lower distance = better match
        })
    
    return formatted_results