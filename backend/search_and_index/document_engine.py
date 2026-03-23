import os
import fitz
import frontmatter

if __package__:
    from .semantic_engine import save_to_vector_db, save_summary_vector
    from .summarizer import summary_generator
    from .sql_database import save_doc_to_db
else:
    from semantic_engine import save_to_vector_db, save_summary_vector
    from summarizer import summary_generator
    from sql_database import save_doc_to_db


def process_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    with open(file_path, "r", encoding="utf-8") as f:
        if ext == ".md":
            post = frontmatter.load(f)
            content = post.content
        else:
            content = f.read()

    segments = []
    chunks = content.split("\n\n")
    for chunk in chunks:
        if chunk.strip():
            segments.append({
                "text": chunk.strip(),
                "page": 1  # flat files don't have pages
            })

    file_name = os.path.basename(file_path)
    summary_text = summary_generator(segments)
    media_id = save_doc_to_db(file_path, file_name, segments, source_type="note", summary=summary_text)

    if media_id:
        save_to_vector_db(media_id, file_name, file_path, segments, summary=summary_text)
        save_summary_vector(media_id, file_name, summary_text)
    
    return media_id


def process_pdf(file_path):
    document = fitz.open(file_path)
    segments = []
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        text = page.get_text("text").strip()
        if text:
            segments.append({
                "text": text,
                "page": page_num + 1
            })
    document.close()

    file_name = os.path.basename(file_path)
    summary_text = summary_generator(segments)
    media_id = save_doc_to_db(file_path, file_name, segments, source_type="pdf", summary=summary_text)

    if media_id:
        save_to_vector_db(media_id, file_name, file_path, segments, summary=summary_text)
        save_summary_vector(media_id, file_name, summary_text)

    return media_id

