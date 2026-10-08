
from __future__ import annotations

from typing import Any

import pandas as pd


def analyse_missingness(
    dataframe: pd.DataFrame,
    top_n_patterns: int = 10,
) -> dict[str, Any]:
    """
    Analyse missing values across columns, rows,
    and recurring missingness patterns.

    Uses pandas missing-value semantics:
    None, NaN, NaT and pd.NA are missing.
    Blank strings are not treated as missing.

    Does not modify the original dataframe.
    """

    if top_n_patterns < 1:
        raise ValueError(
            "top_n_patterns must be at least 1"
        )

    if not dataframe.columns.is_unique:
        raise ValueError(
            "Column names must be unique"
        )

    total_rows = len(dataframe)
    total_columns = len(dataframe.columns)
    total_cells = total_rows * total_columns

    missing_mask = dataframe.isna()

    missing_cells = int(
        missing_mask.to_numpy().sum()
    )

    missing_percentage = (
        round(100 * missing_cells / total_cells, 2)
        if total_cells > 0
        else 0.0
    )

    columns: list[dict[str, Any]] = []

    for column in dataframe.columns:
        count = int(missing_mask[column].sum())

        columns.append({
            "column": str(column),
            "missing_count": count,
            "missing_percentage": (
                round(100 * count / total_rows, 2)
                if total_rows > 0
                else 0.0
            ),
            "non_missing_count": total_rows - count,
        })

    columns.sort(
        key=lambda item: (
            -item["missing_count"],
            item["column"],
        )
    )

    row_missing_counts = missing_mask.sum(
        axis=1
    )

    incomplete_rows = int(
        (row_missing_counts > 0).sum()
    )

    complete_rows = total_rows - incomplete_rows

    row_distribution = [
        {
            "missing_columns": int(count),
            "row_count": int(frequency),
        }
        for count, frequency in sorted(
            row_missing_counts.value_counts().items()
        )
    ]

    patterns: list[dict[str, Any]] = []

    if total_rows > 0:
        pattern_counts: dict[
            tuple[str, ...], int
        ] = {}

        for row in missing_mask.itertuples(
            index=False,
            name=None,
        ):
            missing_columns = tuple(
                str(column)
                for column, is_missing in zip(
                    dataframe.columns,
                    row,
                )
                if is_missing
            )

            pattern_counts[missing_columns] = (
                pattern_counts.get(
                    missing_columns,
                    0,
                ) + 1
            )

        sorted_patterns = sorted(
            pattern_counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )

        for missing_columns, count in (
            sorted_patterns[:top_n_patterns]
        ):
            patterns.append({
                "missing_columns": list(
                    missing_columns
                ),
                "row_count": count,
                "percentage": round(
                    100 * count / total_rows,
                    2,
                ),
            })

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "missing_percentage": missing_percentage,
        "complete_rows": complete_rows,
        "incomplete_rows": incomplete_rows,
        "incomplete_row_percentage": (
            round(
                100 * incomplete_rows / total_rows,
                2,
            )
            if total_rows > 0
            else 0.0
        ),
        "columns": columns,
        "row_distribution": row_distribution,
        "patterns": patterns,
    }
