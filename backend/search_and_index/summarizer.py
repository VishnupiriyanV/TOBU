from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

if __package__:
    from backend.search_and_index.model_downloader import MODEL_SUMMARIZER_PATH
else:
    from model_downloader import MODEL_SUMMARIZER_PATH

import os


_tokenizer = None
_model = None

def get_summarizer():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        if not os.path.exists(MODEL_SUMMARIZER_PATH):
            raise RuntimeError(f"Summarizer model not found at {MODEL_SUMMARIZER_PATH}. Please run onboarding.")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_SUMMARIZER_PATH, local_files_only=True)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_SUMMARIZER_PATH, local_files_only=True)
    return _tokenizer, _model

def summary_generator(data):
    tokenizer, model = get_summarizer()
    if isinstance(data, str):
        chunks = data
    else:
        chunks =" ".join([seg["text"] for seg in data])
    tokens = tokenizer.encode(chunks, add_special_tokens=True)
    max_tokens = 1024
    final_chunks = []
    for i in range(0, len(tokens), max_tokens):
        token_chunk = tokens[i:i + max_tokens]
        inputs = {"input_ids": torch.tensor([token_chunk]), 
                  "attention_mask": torch.ones(1, len(token_chunk), dtype=torch.long)}
        summary_ids = model.generate(inputs["input_ids"], attention_mask=inputs["attention_mask"], do_sample=False)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        final_chunks.append(summary)
    final_sentence = " ".join(final_chunks)
    return final_sentence
    

















    


    
