import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from groq import Groq

load_dotenv()
api_key  = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=api_key)

prev_summaries = []
def summarize_text(text):
    if not text:
        return None  
    try:
        context_summaries = "\n".join(prev_summaries[-5:])
        messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant summarizing only educational text. "
                        "Only respond if the text appears relevant to academic subjects; "
                        "if not, do not generate any response. Summarize in a brief, clear format."
                        "dont forget to give heading for the summarzized content"
                        "use previous context to avoid repetition and enhance the response quality"
                        f"\nPrevious context:\n{context_summaries}\n"
                        
                    )
                },
                 {"role": "user", "content": text}
        
        ]
        completion = client.chat.completions.create(
            messages= messages,
            model="llama3-70b-8192",
            max_tokens=400,
            temperature=0.5,
        )

        summary = completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("Error during summarization:", e)
        return "Summarization error occurred."

