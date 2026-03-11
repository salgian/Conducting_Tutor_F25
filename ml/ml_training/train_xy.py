"""
train.py
--------
Training loop for the beat detection model.

Usage:
    python train.py
"""

import os
import numpy as np
from tensorflow.keras import callbacks

from model import build_model

# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data_xy")
MODEL_DIR  = os.path.join(SCRIPT_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "beat_detector_xy.keras")

EPOCHS     = 100
BATCH_SIZE = 32


# ── Data loading ─────────────────────────────────────────────────────────────

def load_training_data():
    """Load the prepared sequence arrays from disk."""
    X_train = np.load(os.path.join(DATA_DIR, "X_train.npy"))
    y_train = np.load(os.path.join(DATA_DIR, "y_train.npy"))
    X_val   = np.load(os.path.join(DATA_DIR, "X_val.npy"))
    y_val   = np.load(os.path.join(DATA_DIR, "y_val.npy"))
    return X_train, y_train, X_val, y_val


# ── Callbacks ────────────────────────────────────────────────────────────────

def create_callbacks():
    """Create the EarlyStopping and ReduceLROnPlateau callbacks."""
    return [
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=10,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1,
        ),
    ]


# ── Training ─────────────────────────────────────────────────────────────────

def train_model(X_train, y_train, X_val, y_val):
    """Build, train, and save the model. Returns the training history."""
    seq_len, n_features = X_train.shape[1], X_train.shape[2]
    model = build_model(seq_len, n_features)
    model.summary()

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=create_callbacks(),
        verbose=1,
    )

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\n  [OK] Model saved to {MODEL_PATH}\n")

    return history


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    print("\n=== Training beat detector ===\n")

    X_train, y_train, X_val, y_val = load_training_data()
    print(f"  X_train : {X_train.shape}")
    print(f"  X_val   : {X_val.shape}")

    train_model(X_train, y_train, X_val, y_val)


if __name__ == "__main__":
    main()
