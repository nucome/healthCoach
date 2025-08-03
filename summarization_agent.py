import datetime
import time

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english").to(device)


def analyze_sentiment(sentences):
    results = []
    for sentence in sentences:
        inputs = tokenizer(sentence, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
        outputs = model(**inputs)
        probabilitys = torch.softmax(outputs.logits, dim=-1)
        sentiment = "Positive" if torch.argmax(probabilitys) == 1 else "Negative"
        results.append({"sentence": sentence, "sentiment": sentiment})

    return results


class SentimentAnalysisAgent:
    def __init__(self, data_source, interval=10):
        self.data_source = data_source
        self.interval = interval

    def run(self):
        while True:
            sentences = self.data_source()  # Call the function to get the sentences
            if not sentences:
                print(f"[{datetime.datetime.now()}]No sentences to analyze. Waiting for new data...")
            else:
                print(f"[{datetime.datetime.now()}]Analyzing {len(sentences)} sentences...")
                results = analyze_sentiment(sentences)
                for result in results:
                    print(f"Sentence: {result['sentence']}, Sentiment: {result['sentiment']}\n")
            time.sleep(self.interval)


def fetch_sentences():
    # This function should fetch sentences from a data source.
    # For demonstration, we return a static list of sentences.
    import random
    sample_sentences = [
        "The stock market is performing well today.",
        "I am not happy with the current economic situation.",
        "The new policy has had a positive impact on the community.",
        "There are concerns about the rising inflation rates."
    ]
    return random.sample(sample_sentences, random.randint(0, len(sample_sentences)))


if __name__ == "__main__":
    agent = SentimentAnalysisAgent(fetch_sentences, interval=10)
    agent.run()
