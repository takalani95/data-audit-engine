
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


def analyse_numeric_distribution(
    series: pd.Series,
    bins: int = 20,
) -> dict[str, Any]:
    """Summarise a numeric distribution without modifying source data."""

    if bins < 1:
        raise ValueError("bins must be at least 1")

    if not is_numeric_dtype(series) or is_bool_dtype(series):
        raise TypeError("Expected a numeric column")

    numeric = pd.to_numeric(series, errors="coerce")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    infinity_count = int(np.isinf(values).sum())
    finite = numeric.replace([np.inf, -np.inf], np.nan).dropna()
    finite = finite.astype(float)

    result: dict[str, Any] = {
        "column": str(series.name),
        "total_rows": len(series),
        "valid_count": len(finite),
        "missing_count": int(series.isna().sum()),
        "non_finite_count": infinity_count,
        "mean": None,
        "median": None,
        "std": None,
        "min": None,
        "q1": None,
        "q3": None,
        "max": None,
        "skewness": None,
        "histogram_counts": [],
        "histogram_edges": [],
    }

    if finite.empty:
        return result

    result.update({
        "mean": float(finite.mean()),
        "median": float(finite.median()),
        "std": float(finite.std()) if len(finite) > 1 else None,
        "min": float(finite.min()),
        "q1": float(finite.quantile(0.25)),
        "q3": float(finite.quantile(0.75)),
        "max": float(finite.max()),
        "skewness": (
            float(finite.skew())
            if len(finite) >= 3 and finite.nunique() > 1
            else None
        ),
    })

    counts, edges = np.histogram(finite.to_numpy(), bins=bins)
    result["histogram_counts"] = counts.astype(int).tolist()
    result["histogram_edges"] = edges.astype(float).tolist()

    return result


def analyse_categorical_distribution(
    series: pd.Series,
    top_n: int = 15,
) -> dict[str, Any]:
    """Summarise category frequencies without modifying source data."""

    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    non_null = series.dropna()
    labels = non_null.map(str)
    frequencies = labels.value_counts()

    categories = [
        {
            "category": str(category),
            "count": int(count),
            "percentage": round(
                100 * int(count) / len(non_null), 2
            ),
        }
        for category, count in frequencies.head(top_n).items()
    ]

    return {
        "column": str(series.name),
        "total_rows": len(series),
        "non_null_count": len(non_null),
        "missing_count": int(series.isna().sum()),
        "unique_count": int(labels.nunique()),
        "categories": categories,
        "other_categories_count": max(
            0, len(frequencies) - top_n
        ),
    }
