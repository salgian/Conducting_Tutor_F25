"""
evaluate.py
-----------
Evaluate the trained beat-detection model on the validation set.
Prints a classification report and confusion matrix.

Usage:
    python evaluate.py
"""

import os
import numpy as np
from tensorflow import keras
from sklearn.metrics import classification_report, confusion_matrix

# ── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "data_xy")
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "beat_detector_xy.keras")
THRESHOLD  = 0.5


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_validation_data():
    """Load the validation arrays from disk."""
    X_val = np.load(os.path.join(DATA_DIR, "X_val.npy"))
    y_val = np.load(os.path.join(DATA_DIR, "y_val.npy"))
    return X_val, y_val


def predict(model, X_val):
    """Run the model on validation data and return binary predictions."""
    y_prob = model.predict(X_val, verbose=0).flatten()
    y_pred = (y_prob >= THRESHOLD).astype(int)
    return y_pred


def print_report(y_true, y_pred):
    """Print the classification report."""
    print("Classification Report")
    print("-" * 55)
    print(classification_report(
        y_true, y_pred,
        target_names=["no-beat", "beat"],
        digits=3,
    ))


def print_confusion_matrix(y_true, y_pred):
    """Print a formatted confusion matrix."""
    print("Confusion Matrix")
    print("-" * 55)
    cm = confusion_matrix(y_true, y_pred)
    print(f"  {'':>12} predicted")
    print(f"  {'':>12} no-beat   beat")
    print(f"  actual no-beat  {cm[0,0]:>6}   {cm[0,1]:>6}")
    print(f"  actual beat     {cm[1,0]:>6}   {cm[1,1]:>6}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Evaluating beat detector ===\n")

    model = keras.models.load_model(MODEL_PATH)
    X_val, y_val = load_validation_data()
    y_true = y_val.astype(int)
    y_pred = predict(model, X_val)

    print_report(y_true, y_pred)
    print_confusion_matrix(y_true, y_pred)


if __name__ == "__main__":
    main()
