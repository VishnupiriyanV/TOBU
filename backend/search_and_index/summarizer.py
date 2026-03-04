
from transformers import pipeline
text="""On 25 March 2015, amid the Asia leg of their tour, the band announced Malik's departure
 with an official statement. "I'd like to apologise to the fans if I've let anyone down, but I have 
 to do what feels right in my heart", Malik said in the statement. "I am leaving because I want to be a 
 normal 22-year-old who is able to relax and have some private time out of the spotlight. I know I have
   four friends for life in Louis, Liam, Harry and Niall. I know they will continue to be the best band 
   in the world.[128][129] In a subsequent interview,
 Malik denied rumours of a rift between the members and said"""


pipe = pipeline(model="sshleifer/distilbart-cnn-6-6")
def summary_generator(data):
    chunks =" ".join([seg["text"] for seg in data])
    
    
result = pipe(text, max_length=20, min_length=5, do_sample=False)
print(result[0]['summary_text'])
    


    
