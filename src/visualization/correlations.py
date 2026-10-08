
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_numeric_dtype,
)


def analyse_correlations(
    dataframe: pd.DataFrame,
    method: str = "pearson",
    min_pairs: int = 8,
    excluded_columns: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate deterministic pairwise correlations.

    Only numeric, non-boolean columns are considered.
    Explicitly excluded columns are not analysed.

    Non-finite observations are treated as unavailable.
    A pair requires at least min_pairs complete records
    and variation in both columns.

    The source dataframe is never modified.
    """

    if method not in {"pearson", "spearman"}:
        raise ValueError(
            "method must be 'pearson' or 'spearman'"
        )

    if min_pairs < 3:
        raise ValueError(
            "min_pairs must be at least 3"
        )

    excluded = set(excluded_columns or [])

    if not dataframe.columns.is_unique:
        raise ValueError(
            "Column names must be unique"
        )

    numeric_columns = [
        column
        for column in dataframe.columns
        if (
            is_numeric_dtype(dataframe[column])
            and not is_bool_dtype(dataframe[column])
            and column not in excluded
        )
    ]

    clean = pd.DataFrame(index=dataframe.index)

    for column in numeric_columns:
        values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).to_numpy(
            dtype=float,
            na_value=np.nan,
            copy=True,
        )

        # Work only on an independent, writable array.
        values = np.array(
            values,
            dtype=float,
            copy=True,
        )

        values[~np.isfinite(values)] = np.nan
        clean[column] = values

    pairs: list[dict[str, Any]] = []

    for index, first in enumerate(numeric_columns):
        for second in numeric_columns[index + 1:]:

            paired = clean[[first, second]].dropna()
            count = len(paired)

            result: dict[str, Any] = {
                "column_x": str(first),
                "column_y": str(second),
                "paired_count": count,
                "correlation": None,
                "status": "insufficient_data",
            }

            if count < min_pairs:
                pairs.append(result)
                continue

            if (
                paired[first].nunique() < 2
                or paired[second].nunique() < 2
            ):
                result["status"] = "constant_column"
                pairs.append(result)
                continue

            coefficient = paired[first].corr(
                paired[second],
                method=method,
            )

            if (
                pd.notna(coefficient)
                and np.isfinite(coefficient)
            ):
                result["correlation"] = float(
                    np.clip(
                        coefficient,
                        -1.0,
                        1.0,
                    )
                )
                result["status"] = "assessed"
            else:
                result["status"] = "undefined"

            pairs.append(result)

    return {
        "method": method,
        "min_pairs": min_pairs,
        "numeric_columns": [
            str(column)
            for column in numeric_columns
        ],
        "pairs": pairs,
        "assessed_pairs": sum(
            pair["status"] == "assessed"
            for pair in pairs
        ),
        "unassessed_pairs": sum(
            pair["status"] != "assessed"
            for pair in pairs
        ),
    }
