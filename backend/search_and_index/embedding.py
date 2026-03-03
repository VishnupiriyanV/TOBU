
from sentence_transformers import SentenceTransformer


#converts 
def embed(sentences):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    embeddings = model.encode(sentences)
    return embeddings

sentences=eval(input("enter the sentence to be embedded:"))
print(embed(sentences))