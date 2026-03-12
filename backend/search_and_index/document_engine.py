import os
import fitz  
from semantic_engine import save_to_vector_db
from summarizer import summary_generator
from semantic_engine import save_to_vector_db
import frontmatter



def process_pdf(file):
    document = fitz.open(file)
    content =[]
    print(len(document))
    for page_num in range(len(document)):

       page = document.load_page(page_num)
       text = page.get_text("text")

       content.append({
           "text": text.strip(),
           "page": page_num + 1
       })
    summary_text = summary_generator(content)
    return summary_text



def process_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    with open(file_path, "r", encoding="utf-8") as f:
        if ext == ".md":
            # frontmatter for Markdown
            post = frontmatter.load(f)
            content = post.content
            metadata = post.metadata
        else:
            #for txt files
            content = f.read()
            metadata = {"source": "plain_text"} 

    
    segments = []
    chunks = content.split("\n\n")
    for chunk in chunks:
        if chunk.strip():
            segment = {
                "text": chunk,
                "type": "text_chunk"
            }
            segments.append(segment)
    
    #media_id = save_doc_to_db(file_path, "text")
    save_to_vector_db(media_id, file_path, segments, type="note")

