from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "sshleifer/distilbart-cnn-6-6"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def summary_generator(data):
    if isinstance(data, str):
        chunks = data
    else:
        chunks =" ".join([seg["text"] for seg in data])
    max_ch=4000
    final_chunks=[]
    cursor=0
    while(cursor<len(chunks)):
        
        end_point=cursor+max_ch
        sub_chunks=chunks[cursor:end_point]
        if end_point<len(chunks):
            actual_ending=sub_chunks.rfind(' ')
            if actual_ending != -1:
                sub_chunks=sub_chunks[:actual_ending]
                cursor+=(actual_ending+1)
            else:
                cursor+=max_ch
        else:
            cursor=len(chunks)
        inputs = tokenizer(sub_chunks, return_tensors="pt", max_length=1024, truncation=True,padding="max_length")
        summary_ids = model.generate(inputs["input_ids"],attention_mask=inputs["attention_mask"], do_sample=False)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        final_chunks.append(summary)
    final_sentence =" ".join([seg for seg in final_chunks])
    return final_sentence




















    


    
