
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from src.visualization.duration_intelligence import analyse_duration_column
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


DATE_KEYWORDS = (
    "date",
    "time",
    "timestamp",
    "created",
    "received",
)

IDENTIFIER_KEYWORDS = (
    "identifier",
    "reference",
    "merchant number",
    "merchant no",
    "merchant id",
    "case no",
    "case number",
    "account number",
    "account no",
    "account id",
    "store id",
    "terminal id",
    "transaction id",
)

CATEGORY_KEYWORDS = (
    "severity",
    "level",
    "status",
    "category",
    "priority",
    "rating",
    "code",
)


def analyse_column_intelligence(
    series: pd.Series,
    max_categories: int = 15,
) -> dict[str, Any]:
    """
    Classify a column and recommend a visualization.

    This is a deterministic heuristic engine, not
    a machine-learning classifier.

    Does not modify the original series.
    """

    if not isinstance(series, pd.Series):
        raise TypeError("Expected a pandas Series")

    if max_categories < 2:
        raise ValueError(
            "max_categories must be at least 2"
        )

    column = str(series.name or "Unknown")
    normalized_name = column.lower().strip()

    total_count = len(series)
    missing_count = int(series.isna().sum())
    valid = series.dropna()
    valid_count = len(valid)

    result: dict[str, Any] = {
        "column": column,
        "dtype": str(series.dtype),
        "total_count": total_count,
        "valid_count": valid_count,
        "missing_count": missing_count,
        "unique_count": int(valid.nunique()),
        "semantic_type": "unknown",
        "recommended_analysis": None,
        "recommended_chart": None,
        "reason": "",
    }

    if valid_count == 0:
        result["reason"] = (
            "No non-missing values are available."
        )
        return result

    # Detect identifier-like columns before numeric analysis.
    if any(
        keyword in normalized_name
        for keyword in IDENTIFIER_KEYWORDS
    ):
        result.update({
            "semantic_type": "identifier",
            "reason": (
                "Column name suggests an identifier. "
                "Identifiers should not be interpreted "
                "as continuous measurements."
            ),
        })
        return result

    # Native datetime columns.
    if is_datetime64_any_dtype(series):
        result.update({
            "semantic_type": "datetime",
            "recommended_analysis": "time_series",
            "recommended_chart": "line",
            "reason": "Native datetime column detected.",
        })
        return result

    # Boolean columns.
    if is_bool_dtype(series):
        result.update({
            "semantic_type": "categorical",
            "recommended_analysis": "categorical_distribution",
            "recommended_chart": "bar",
            "reason": "Boolean values represent categories.",
        })
        return result

    # Numeric columns.
    if is_numeric_dtype(series):
        numeric = pd.to_numeric(
            valid,
            errors="coerce",
        )

        numeric = numeric.replace(
            [np.inf, -np.inf],
            np.nan,
        ).dropna()

        if numeric.empty:
            result["reason"] = (
                "No finite numeric values are available."
            )
            return result

        unique_values = numeric.nunique()

        is_discrete = (
            unique_values <= max_categories
            and np.all(
                np.isclose(
                    numeric.to_numpy(dtype=float),
                    np.round(
                        numeric.to_numpy(dtype=float)
                    ),
                )
            )
        )

        is_named_category = any(
            keyword in normalized_name
            for keyword in CATEGORY_KEYWORDS
        )

        if is_named_category or is_discrete:
            result.update({
                "semantic_type": "discrete_numeric",
                "recommended_analysis": (
                    "categorical_distribution"
                ),
                "recommended_chart": "bar",
                "reason": (
                    "Numeric values appear to represent "
                    "a small set of categories."
                ),
            })
        else:
            result.update({
                "semantic_type": "continuous_numeric",
                "recommended_analysis": (
                    "numeric_distribution"
                ),
                "recommended_chart": "histogram",
                "reason": (
                    "Numeric measurements are suitable "
                    "for distribution analysis."
                ),
            })

        return result

    # Duration-like text columns.
    duration_keywords = (
        "duration",
        "time to",
        "elapsed",
        "turnaround",
        "response time",
        "resolution time",
    )

    if any(
        keyword in normalized_name
        for keyword in duration_keywords
    ):
        duration_result = analyse_duration_column(series)

        success_rate = (
            duration_result["valid_count"] / valid_count
        )

        if success_rate >= 0.90:
            result.update({
                "semantic_type": "duration",
                "recommended_analysis": (
                    "duration_distribution"
                ),
                "recommended_chart": "histogram",
                "reason": (
                    "Duration values can be converted "
                    "to minutes for numerical analysis. "
                    f"Parse success among non-missing "
                    f"values: {success_rate:.1%}."
                ),
            })
            return result

        result.update({
            "semantic_type": "categorical",
            "recommended_analysis": "categorical_distribution",
            "recommended_chart": "bar",
            "reason": (
                "Duration-like column, but only "
                f"{success_rate:.1%} of non-missing values "
                "could be parsed. Review invalid values "
                "before treating this as a numerical duration."
            ),
        })
        return result

    # Date-like text columns.
    if any(
        keyword in normalized_name
        for keyword in DATE_KEYWORDS
    ):
        sample = valid.head(100)

        parsed = pd.to_datetime(
            sample,
            errors="coerce",
        )

        success_rate = parsed.notna().mean()

        if success_rate >= 0.8:
            result.update({
                "semantic_type": "datetime",
                "recommended_analysis": "time_series",
                "recommended_chart": "line",
                "reason": (
                    "Column name and sampled values "
                    "suggest datetime information."
                ),
            })
            return result

    # General categorical columns.
    result.update({
        "semantic_type": "categorical",
        "recommended_analysis": (
            "categorical_distribution"
        ),
        "recommended_chart": "bar",
        "reason": (
            "Text or other non-numeric values "
            "are suitable for category frequencies."
        ),
    })

    return result
