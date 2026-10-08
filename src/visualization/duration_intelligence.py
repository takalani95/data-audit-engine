
from __future__ import annotations

import math
import re
from datetime import timedelta
from numbers import Real
from typing import Any

import numpy as np
import pandas as pd


DURATION_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(days?|hours?|hrs?|minutes?|mins?|seconds?|secs?)\b",
    re.IGNORECASE,
)

UNIT_MINUTES = {
    "day": 1440,
    "days": 1440,
    "hour": 60,
    "hours": 60,
    "hr": 60,
    "hrs": 60,
    "minute": 1,
    "minutes": 1,
    "min": 1,
    "mins": 1,
    "second": 1 / 60,
    "seconds": 1 / 60,
    "sec": 1 / 60,
    "secs": 1 / 60,
}


def parse_duration_minutes(value: Any) -> float | None:
    """
    Convert a duration to minutes.

    Numeric values are interpreted as minutes.
    Zero is a valid duration.

    Returns None when the value cannot be
    interpreted safely.
    """

    if pd.isna(value):
        return None

    if isinstance(value, (pd.Timedelta, timedelta)):
        minutes = value.total_seconds() / 60
        return minutes if minutes >= 0 else None

    if isinstance(value, (bool, np.bool_)):
        return None

    if isinstance(value, Real):
        number = float(value)
        return number if math.isfinite(number) and number >= 0 else None

    if not isinstance(value, str):
        return None

    text = value.strip().lower()

    if not text:
        return None

    # A bare numeric string is interpreted as minutes.
    try:
        number = float(text)
        if math.isfinite(number) and number >= 0:
            return number
        return None
    except ValueError:
        pass

    matches = list(DURATION_PATTERN.finditer(text))

    if not matches:
        return None

    # Reject unrecognised text between matched units.
    remainder = DURATION_PATTERN.sub("", text)
    remainder = re.sub(r"[\s,]+", "", remainder)

    if remainder:
        return None

    total_minutes = 0.0

    for match in matches:
        amount = float(match.group(1))
        unit = match.group(2).lower()

        total_minutes += amount * UNIT_MINUTES[unit]

    if not math.isfinite(total_minutes):
        return None

    return total_minutes


def analyse_duration_column(
    series: pd.Series,
) -> dict[str, Any]:
    """
    Analyse duration values without modifying
    the original series.
    """

    if not isinstance(series, pd.Series):
        raise TypeError("Expected a pandas Series")

    parsed = series.map(parse_duration_minutes)

    valid = parsed.dropna().astype(float)

    return {
        "column": str(series.name or "Unknown"),
        "total_count": int(len(series)),
        "valid_count": int(len(valid)),
        "invalid_or_missing_count": int(parsed.isna().sum()),
        "parse_success_rate": (
            float(len(valid) / len(series))
            if len(series)
            else 0.0
        ),
        "unit": "minutes",
        "values": valid.tolist(),
        "minimum": float(valid.min()) if len(valid) else None,
        "maximum": float(valid.max()) if len(valid) else None,
        "mean": float(valid.mean()) if len(valid) else None,
        "median": float(valid.median()) if len(valid) else None,
    }
