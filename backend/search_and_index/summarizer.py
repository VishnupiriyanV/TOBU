from transformers import pipeline


summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def get_summary(text):
    input_text = text[:3000] 
    try:
        summary_results = summarizer(
            input_text, 
            do_sample=False
        )
        return summary_results[0]['summary_text']
    except Exception as e:
        return f"generation failed: {str(e)}"


# transcript = "nothing"
# print(get_summary(transcript))