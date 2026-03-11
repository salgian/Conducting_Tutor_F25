"""
build_sequences.py
------------------
Load all training CSVs, extract 11-frame sliding windows, label them as
beat / no-beat, balance the dataset, and save NumPy arrays for training.

Usage:
    python build_sequences.py
"""

import os
import glob
import random
import numpy as np
import pandas as pd

# ── Configuration ────────────────────────────────────────────────────────────

SEQ_LEN      = 11                          # frames per window
FEATURE_COLS = ["x_norm", "y_norm"]
LABEL_COL    = "beat"
VAL_SPLIT    = 0.2                         # fraction held out for validation
SEED         = 42

# Paths (relative to this script's location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, "..", "ml_data_extraction", "training_data")
OUT_DIR    = os.path.join(SCRIPT_DIR, "data_xy")


# ── CSV loading ──────────────────────────────────────────────────────────────

def load_all_csvs(data_dir):
    """Load every CSV in *data_dir* and return a list of DataFrames."""
    pattern = os.path.join(data_dir, "conducting_*.csv")
    paths   = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = [pd.read_csv(p) for p in paths]
    print(f"  Loaded {len(dfs)} CSV files from {data_dir}")
    return dfs


# ── Window extraction ────────────────────────────────────────────────────────

def extract_positive_windows(features, beats, n_frames):
    """
    For each beat frame, create augmented windows with the beat
    at every valid position (indices 1 to SEQ_LEN-2).
    """
    windows = []
    beat_indices = np.where(beats == 1)[0]

    for beat_idx in beat_indices:
        for pos_in_window in range(1, SEQ_LEN - 1):
            start = beat_idx - pos_in_window
            end   = start + SEQ_LEN
            if start < 0 or end > n_frames:
                continue
            windows.append(features[start:end])

    return windows


def extract_negative_windows(features, beats, n_frames):
    """Extract all windows that contain zero beat frames."""
    windows = []
    for start in range(n_frames - SEQ_LEN + 1):
        end = start + SEQ_LEN
        if beats[start:end].sum() == 0:
            windows.append(features[start:end])
    return windows


def extract_windows(dfs):
    """
    From a list of per-session DataFrames, extract positive and negative
    11-frame windows.
    """
    pos_windows = []
    neg_windows = []

    for df in dfs:
        features = df[FEATURE_COLS].values
        beats    = df[LABEL_COL].values.astype(int)
        n_frames = len(df)

        pos_windows.extend(extract_positive_windows(features, beats, n_frames))
        neg_windows.extend(extract_negative_windows(features, beats, n_frames))

    print(f"  Raw positive windows : {len(pos_windows)}")
    print(f"  Raw negative windows : {len(neg_windows)}")
    return pos_windows, neg_windows


# ── Balancing and splitting ──────────────────────────────────────────────────

def balance_classes(pos_windows, neg_windows, seed=SEED):
    """Undersample the majority class to match the minority class."""
    rng = random.Random(seed)
    target = min(len(pos_windows), len(neg_windows))

    if len(pos_windows) > target:
        pos_windows = rng.sample(pos_windows, target)
    if len(neg_windows) > target:
        neg_windows = rng.sample(neg_windows, target)

    print(f"  Balanced to {target} samples per class ({2 * target} total)")
    return pos_windows, neg_windows


def shuffle_and_split(pos_windows, neg_windows, val_split=VAL_SPLIT, seed=SEED):
    """Combine, shuffle, and split into train / validation sets."""
    rng = random.Random(seed)

    X_all = np.array(pos_windows + neg_windows, dtype=np.float32)
    y_all = np.array(
        [1] * len(pos_windows) + [0] * len(neg_windows), dtype=np.float32
    )

    indices = list(range(len(X_all)))
    rng.shuffle(indices)
    X_all = X_all[indices]
    y_all = y_all[indices]

    n_val   = int(len(X_all) * val_split)
    X_val,   y_val   = X_all[:n_val],  y_all[:n_val]
    X_train, y_train = X_all[n_val:],  y_all[n_val:]

    return X_train, y_train, X_val, y_val


# ── Save ─────────────────────────────────────────────────────────────────────

def save_arrays(X_train, y_train, X_val, y_val, out_dir=OUT_DIR):
    """Write the prepared arrays to disk."""
    os.makedirs(out_dir, exist_ok=True)
    np.save(os.path.join(out_dir, "X_train.npy"), X_train)
    np.save(os.path.join(out_dir, "y_train.npy"), y_train)
    np.save(os.path.join(out_dir, "X_val.npy"),   X_val)
    np.save(os.path.join(out_dir, "y_val.npy"),   y_val)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Building sequences ===\n")

    dfs = load_all_csvs(DATA_DIR)
    pos_windows, neg_windows = extract_windows(dfs)
    pos_windows, neg_windows = balance_classes(pos_windows, neg_windows)
    X_train, y_train, X_val, y_val = shuffle_and_split(pos_windows, neg_windows)

    save_arrays(X_train, y_train, X_val, y_val)

    print(f"\n  X_train : {X_train.shape}")
    print(f"  y_train : {y_train.shape}  "
          f"(pos {y_train.sum():.0f} / neg {(1-y_train).sum():.0f})")
    print(f"  X_val   : {X_val.shape}")
    print(f"  y_val   : {y_val.shape}  "
          f"(pos {y_val.sum():.0f} / neg {(1-y_val).sum():.0f})")
    print(f"\n  [OK] Saved to {OUT_DIR}/\n")


if __name__ == "__main__":
    main()
