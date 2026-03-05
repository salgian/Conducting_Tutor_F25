"""
time_signature.py
-----------------
Estimate time signature from detected beat intervals.
"""

import collections
import numpy as np


def estimate_time_signature(beat_intervals):
    """
    Given a list of frame-intervals between consecutive beats,
    try to guess 2/4, 3/4, or 4/4.

    Approach: count how many beats occur per "measure" by looking at
    which intervals are significantly longer (indicating a downbeat /
    measure boundary).
    """
    if len(beat_intervals) < 3:
        return "Not enough beats to estimate"

    median_gap = float(np.median(beat_intervals))

    # Long gaps (> 1.4x median) suggest a measure boundary
    threshold = median_gap * 1.4
    beats_per_measure = []
    current_count = 1

    for gap in beat_intervals:
        if gap > threshold:
            beats_per_measure.append(current_count)
            current_count = 1
        else:
            current_count += 1

    if current_count >= 2:
        beats_per_measure.append(current_count)

    if not beats_per_measure:
        return "4/4"

    counts = collections.Counter(beats_per_measure)
    most_common = counts.most_common(1)[0][0]

    if most_common <= 2:
        return "2/4"
    elif most_common == 3:
        return "3/4"
    else:
        return "4/4"
