# Description: TensorFlow import, version check, and reproducible setup
import tensorflow as tf
print("TensorFlow:", tf.__version__)
tf.random.set_seed(42)
