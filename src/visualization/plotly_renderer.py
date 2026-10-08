
from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go


SUPPORTED_CHART_TYPES = {
    "histogram",
    "bar",
    "heatmap",
    "missingness_bar",
    "line",
}


def render_chart(
    chart_specification: dict[str, Any],
) -> go.Figure:
    """
    Convert a chart specification into a Plotly figure.

    Does not modify the supplied specification.
    """

    if not isinstance(chart_specification, dict):
        raise TypeError(
            "chart_specification must be a dictionary"
        )

    chart_type = chart_specification.get("chart_type")

    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"Unsupported chart type: {chart_type}"
        )

    title = chart_specification.get("title", "")
    x_label = chart_specification.get("x_label", "")
    y_label = chart_specification.get("y_label", "")
    data = chart_specification.get("data", {})

    figure = go.Figure()

    if chart_type == "histogram":
        counts = data.get("counts", [])
        edges = data.get("edges", [])

        if counts and len(edges) != len(counts) + 1:
            raise ValueError(
                "Histogram edges must contain one more "
                "element than counts"
            )

        if counts:
            centers = [
                (edges[i] + edges[i + 1]) / 2
                for i in range(len(counts))
            ]
            widths = [
                edges[i + 1] - edges[i]
                for i in range(len(counts))
            ]

            figure.add_trace(
                go.Bar(
                    x=centers,
                    y=counts,
                    width=widths,
                    name="Frequency",
                    marker_line_width=0.5,
                )
            )

    elif chart_type == "bar":
        figure.add_trace(
            go.Bar(
                x=[item["category"] for item in data],
                y=[item["count"] for item in data],
                name="Count",
            )
        )

    elif chart_type == "missingness_bar":
        figure.add_trace(
            go.Bar(
                x=[item["column"] for item in data],
                y=[
                    item["missing_percentage"]
                    for item in data
                ],
                name="Missing %",
            )
        )

    elif chart_type == "line":
        figure.add_trace(
            go.Scatter(
                x=[item["period"] for item in data],
                y=[item["count"] for item in data],
                mode="lines+markers",
                name="Count",
                line={"width": 2},
                marker={"size": 7},
                connectgaps=False,
            )
        )

        figure.update_xaxes(type="date")

    elif chart_type == "heatmap":
        columns = sorted({
            name
            for item in data
            for name in (
                item["column_x"],
                item["column_y"],
            )
        })

        if columns:
            index = {
                column: position
                for position, column in enumerate(columns)
            }

            matrix = np.full(
                (len(columns), len(columns)),
                np.nan,
            )

            for item in data:
                coefficient = item["correlation"]

                if (
                    item["status"] == "assessed"
                    and coefficient is not None
                ):
                    i = index[item["column_x"]]
                    j = index[item["column_y"]]

                    matrix[i, j] = coefficient
                    matrix[j, i] = coefficient

            for position in range(len(columns)):
                matrix[position, position] = 1.0

            figure.add_trace(
                go.Heatmap(
                    z=matrix,
                    x=columns,
                    y=columns,
                    zmin=-1,
                    zmax=1,
                    colorscale="RdBu",
                    reversescale=True,
                    colorbar={
                        "title": "Correlation"
                    },
                    hoverongaps=False,
                )
            )

    figure.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_white",
        height=480,
        margin={
            "l": 40,
            "r": 30,
            "t": 70,
            "b": 70,
        },
    )

    return figure
