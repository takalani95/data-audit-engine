
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.visualization.duration_intelligence import (
    analyse_duration_column,
)


def create_duration_histogram(
    series: pd.Series,
    bins: int = 30,
) -> go.Figure:
    """Create a histogram of durations in minutes."""

    if not isinstance(series, pd.Series):
        raise TypeError("Expected a pandas Series")

    if bins < 2:
        raise ValueError("bins must be at least 2")

    result = analyse_duration_column(series)

    if not result["values"]:
        raise ValueError("No valid durations available")

    chart_data = pd.DataFrame({
        "Duration (minutes)": result["values"]
    })

    fig = px.histogram(
        chart_data,
        x="Duration (minutes)",
        nbins=bins,
        title=f"Duration Distribution — {result['column']}",
    )

    fig.update_layout(
        xaxis_title="Duration (minutes)",
        yaxis_title="Number of records",
        bargap=0.05,
    )

    return fig
