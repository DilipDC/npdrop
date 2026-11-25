# Description: Basic text tokenization with TensorFlow Keras
from tensorflow.keras.preprocessing.text import Tokenizer
texts = ["I love machine learning", "Python makes ML easier"]
tokenizer = Tokenizer(num_words=5000, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
print(sequences)
