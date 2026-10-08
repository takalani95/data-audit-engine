
from __future__ import annotations

from typing import Any

import pandas as pd

from src.visualization.column_intelligence import (
    analyse_column_intelligence,
)


def analyse_dataset_intelligence(
    dataframe: pd.DataFrame,
    max_categories: int = 15,
) -> dict[str, Any]:
    """
    Analyse every column in a dataset and create
    a chart recommendation catalogue.

    Does not modify the original dataframe.
    """

    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame")

    if max_categories < 2:
        raise ValueError(
            "max_categories must be at least 2"
        )

    columns = []

    for index in range(dataframe.shape[1]):
        series = dataframe.iloc[:, index].copy()
        series.name = str(dataframe.columns[index])

        result = analyse_column_intelligence(
            series,
            max_categories=max_categories,
        )

        result["column_index"] = index
        columns.append(result)

    recommended = [
        result
        for result in columns
        if result["recommended_chart"] is not None
    ]

    skipped = [
        result
        for result in columns
        if result["recommended_chart"] is None
    ]

    chart_counts: dict[str, int] = {}

    for result in recommended:
        chart = result["recommended_chart"]
        chart_counts[chart] = (
            chart_counts.get(chart, 0) + 1
        )

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(dataframe.shape[1]),
        "recommended_count": len(recommended),
        "skipped_count": len(skipped),
        "chart_counts": chart_counts,
        "columns": columns,
        "recommended": recommended,
        "skipped": skipped,
    }
