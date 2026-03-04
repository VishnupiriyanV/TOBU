from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_name = "sshleifer/distilbart-cnn-6-6"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)





def summary_generator(data):
    chunks =" ".join([seg["text"] for seg in data])
    max_ch=4000
    final_chunks=[]
    for i in range(0,len(chunks),max_ch):
        sub_chunks=chunks[i:(max_ch+i)]
        
        inputs = tokenizer(sub_chunks, return_tensors="pt", max_length=1024, truncation=True)
        summary_ids = model.generate(inputs["input_ids"], do_sample=False)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        final_chunks.append(summary)
    final_sentence =" ".join([seg for seg in final_chunks])
    return final_sentence





















    


    
