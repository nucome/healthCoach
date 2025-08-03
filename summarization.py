from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("t5-base")

def summarize_text(text):
    inputs = tokenizer.encode("summarize: Focus on key impacts and industries " + text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(inputs, max_length=40, min_length=10, length_penalty=3.5, num_beams=5, early_stopping=True)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    unique_sentences = list(dict.fromkeys(summary.split('. ')))  # Remove duplicates while preserving order
    return '. '.join(unique_sentences)

if __name__ == "__main__":
    text = "The stock market has seen significant fluctuations in recent months, with technology stocks leading the way. Investors are concerned about inflation and interest rates, which could impact economic growth. The energy sector is also experiencing volatility due to geopolitical tensions."
    summary = summarize_text(text)
    print("Summary:", summary)  # Example usage