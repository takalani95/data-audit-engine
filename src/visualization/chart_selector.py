
from __future__ import annotations

from typing import Any


SUPPORTED_ANALYSES = {
    "numeric_distribution": "histogram",
    "categorical_distribution": "bar",
    "correlation": "heatmap",
    "missingness": "missingness_bar",
}


def select_chart(
    analysis_type: str,
    analysis_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Choose a visualization from a known analysis type.

    Returns a chart specification, not a rendered chart.
    Does not modify the supplied analysis result.
    """

    if analysis_type not in SUPPORTED_ANALYSES:
        raise ValueError(
            f"Unsupported analysis type: {analysis_type}"
        )

    if not isinstance(analysis_result, dict):
        raise TypeError(
            "analysis_result must be a dictionary"
        )

    chart_type = SUPPORTED_ANALYSES[analysis_type]

    if analysis_type == "numeric_distribution":
        column = analysis_result.get("column", "Unknown")

        return {
            "chart_type": chart_type,
            "title": f"Distribution of {column}",
            "x_label": str(column),
            "y_label": "Frequency",
            "data": {
                "counts": list(
                    analysis_result.get(
                        "histogram_counts", []
                    )
                ),
                "edges": list(
                    analysis_result.get(
                        "histogram_edges", []
                    )
                ),
            },
        }

    if analysis_type == "categorical_distribution":
        column = analysis_result.get("column", "Unknown")

        categories = analysis_result.get(
            "categories", []
        )

        return {
            "chart_type": chart_type,
            "title": f"Category Frequencies: {column}",
            "x_label": "Category",
            "y_label": "Count",
            "data": [
                {
                    "category": item["category"],
                    "count": item["count"],
                }
                for item in categories
            ],
        }

    if analysis_type == "correlation":
        return {
            "chart_type": chart_type,
            "title": (
                f"{analysis_result.get('method', 'pearson').title()}"
                " Correlation Heatmap"
            ),
            "x_label": "Variables",
            "y_label": "Variables",
            "data": [
                {
                    "column_x": item["column_x"],
                    "column_y": item["column_y"],
                    "correlation": item["correlation"],
                    "status": item["status"],
                }
                for item in analysis_result.get("pairs", [])
            ],
        }

    return {
        "chart_type": chart_type,
        "title": "Missing Values by Column",
        "x_label": "Column",
        "y_label": "Missing Percentage (%)",
        "data": [
            {
                "column": item["column"],
                "missing_percentage": item[
                    "missing_percentage"
                ],
            }
            for item in analysis_result.get("columns", [])
        ],
    }
