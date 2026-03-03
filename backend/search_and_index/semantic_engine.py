
from sentence_transformers import SentenceTransformer
import lancedb


#converts text to embedding
def embed(sentences):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(sentences)
    return embeddings




def save_to_vector_db(media_id,file_name,file_path,transcript_data,db_path="vector_data"):
    
    windowed_text_lists = sentence_window(transcript_data)

    texts_to_embed = [" ".join(window) for window in windowed_text_lists]

    #generate the embedding
    vector_matrix = embed(texts_to_embed)
    embeddings = vector_matrix.tolist()

    #map data

    data = []
    for i in range(len(transcript_data)):
        data.append({
            "vector" : embeddings[i],
            "text" : transcript_data[i]["text"],
            "context": texts_to_embed[i],
            "start" : transcript_data[i]["start"]
            "file_name": file_name,
            "file_path":file_path,
            "media_id" : media_id

        })

    # storing the data in lancedb

    db = lancedb.connect(db_path)
    table_name = "semantic_segments"

    if table_name in db.table_name():
        table = db.open_table(table_name)
        table.add(data)
    else:
        db.create_table(table_name,data=data)



    





