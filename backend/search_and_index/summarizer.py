from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

model_name = "sshleifer/distilbart-cnn-6-6"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def summary_generator(data):
    if isinstance(data, str):
        chunks = data
    else:
        chunks =" ".join([seg["text"] for seg in data])
    tokens = tokenizer.encode(chunks)
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
    

















    


    
