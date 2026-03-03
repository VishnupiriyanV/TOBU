
from sentence_transformers import SentenceTransformer


#converts text to embedding
def embed(sentences):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(sentences)
    return embeddings

def save_to_vector_db(media_id)