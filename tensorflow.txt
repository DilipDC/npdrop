import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense
import matplotlib.pyplot as plt
import numpy as np

# 1. Load & normalize MNIST (28x28 grayscale images, labels 0-9)
(x_train, y_train), (x_test, y_test) = keras.datasets.mnist.load_data()
x_train = x_train.reshape(-1, 28, 28, 1) / 255.0
x_test = x_test.reshape(-1, 28, 28, 1) / 255.0

# 2. Build CNN model
model = Sequential([
    Input(shape=(28, 28, 1)),
    Conv2D(32, 3, activation='relu'),
    MaxPooling2D(),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(10, activation='softmax')
])

# 3. Compile & train
model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)
model.fit(x_train, y_train, epochs=5)

# 4. Predict on test set
y_pred = model.predict(x_test)

# 5. Plot sample training image
plt.imshow(x_train[4].squeeze(), cmap='gray')
plt.axis('off')
plt.show()

# 6. Plot first 10 test images with predicted digit label
plt.figure(figsize=(10, 3))
for i in range(10):
    plt.subplot(1, 10, i + 1)
    plt.imshow(x_test[i].squeeze(), cmap='gray')
    plt.title(f"Pred: {np.argmax(y_pred[i])}")
    plt.axis('off')
plt.tight_layout()
plt.show()