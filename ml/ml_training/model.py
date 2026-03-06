"""
model.py
--------
Keras LSTM model architecture for binary beat detection.
"""

from tensorflow import keras
from tensorflow.keras import layers


def build_model(seq_len, n_features):
    """
    Build an LSTM-based binary classifier.

    Architecture:
        Input  -> (seq_len, n_features)
        LSTM   -> 64 units
        Drop   -> 0.3
        Dense  -> 32, ReLU
        Drop   -> 0.2
        Dense  -> 1, Sigmoid
    """
    model = keras.Sequential([
        layers.Input(shape=(seq_len, n_features)),
        layers.LSTM(64),
        layers.Dropout(0.3),
        layers.Dense(32, activation="relu"),
        layers.Dropout(0.2),
        layers.Dense(1, activation="sigmoid"),
    ])

    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )
    return model
