
from sentence_transformers import SentenceTransformer
import lancedb


#converts text to embedding
def embed(sentences):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(sentences)
    return embeddings


def sentence_window(data):
    final_list=[]
    chunks = [seg["text"] for seg in data]
    n=len(chunks)
    start_text=list([chunks[0],chunks[1]])
    end_text=list([chunks[n-2],chunks[n-1]])
    final_list.append(start_text)
    for text in range(1,n-1):
        first_sentence=chunks[text-1]
        middle_sentence=chunks[text]
        last_sentence=chunks[text+1]
        final_window=[first_sentence,middle_sentence,last_sentence]
        final_list.append(final_window)
        
    
    
    final_list.append(end_text)

    return final_list

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
            "start" : transcript_data[i]["start"],
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


def semantic_search(query,limit,db_path="vector_data"):
    db = lancedb.connect(db_path)
    table = db.open_table("semantic_segments")
    
    
    query_vector = embed([query])[0].tolist()    
    results = table.search(query_vector).limit(limit).to_list()




    





