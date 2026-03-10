import fitz  
from semantic_engine import save_to_vector_db





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
    
    return content

