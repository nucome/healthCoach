from transformers import AutoModel, AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")
inputs = tokenizer("Hello, world!", return_tensors="pt")

outputs = model(**inputs)
print(outputs.last_hidden_state.shape)  # Should print the shape of the last hidden state
