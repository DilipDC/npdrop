# Description: Normalize text and remove punctuation for NLP
import re
def clean_text(text):
    text = text.lower().strip()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
print(clean_text("Hello, NLP! Visit https://example.com"))
