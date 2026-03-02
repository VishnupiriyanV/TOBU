#for testing the full text search

from backend.search_and_index.sql_database import search_to_json


query1 = "algorithms"

query2 = "manhattan"

query3 = "TED"

print(search_to_json(query3))