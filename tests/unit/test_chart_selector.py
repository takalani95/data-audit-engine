
import copy

import pytest

from src.visualization.chart_selector import (
    select_chart,
)


def test_numeric_distribution_selects_histogram():
    result = {
        "column": "Sales",
        "histogram_counts": [2, 3, 5],
        "histogram_edges": [0, 10, 20, 30],
    }

    chart = select_chart(
        "numeric_distribution",
        result,
    )

    assert chart["chart_type"] == "histogram"
    assert chart["title"] == "Distribution of Sales"
    assert chart["x_label"] == "Sales"
    assert chart["y_label"] == "Frequency"


def test_histogram_preserves_counts_and_edges():
    result = {
        "column": "Revenue",
        "histogram_counts": [4, 6],
        "histogram_edges": [0, 50, 100],
    }

    chart = select_chart(
        "numeric_distribution",
        result,
    )

    assert chart["data"]["counts"] == [4, 6]
    assert chart["data"]["edges"] == [0, 50, 100]


def test_categorical_distribution_selects_bar_chart():
    result = {
        "column": "Bank",
        "categories": [
            {
                "category": "FNB",
                "count": 10,
                "percentage": 50.0,
            },
            {
                "category": "Capitec",
                "count": 10,
                "percentage": 50.0,
            },
        ],
    }

    chart = select_chart(
        "categorical_distribution",
        result,
    )

    assert chart["chart_type"] == "bar"
    assert chart["title"] == "Category Frequencies: Bank"
    assert chart["data"] == [
        {"category": "FNB", "count": 10},
        {"category": "Capitec", "count": 10},
    ]


def test_correlation_selects_heatmap():
    result = {
        "method": "spearman",
        "pairs": [
            {
                "column_x": "Sales",
                "column_y": "Revenue",
                "correlation": 0.85,
                "status": "assessed",
            },
        ],
    }

    chart = select_chart(
        "correlation",
        result,
    )

    assert chart["chart_type"] == "heatmap"
    assert chart["title"] == "Spearman Correlation Heatmap"
    assert chart["data"][0]["correlation"] == 0.85


def test_unassessed_correlations_are_preserved():
    result = {
        "method": "pearson",
        "pairs": [
            {
                "column_x": "A",
                "column_y": "B",
                "correlation": None,
                "status": "insufficient_data",
            },
        ],
    }

    chart = select_chart(
        "correlation",
        result,
    )

    assert chart["data"][0]["correlation"] is None
    assert chart["data"][0]["status"] == "insufficient_data"


def test_missingness_selects_missingness_bar():
    result = {
        "columns": [
            {
                "column": "Merchant Number",
                "missing_count": 5,
                "missing_percentage": 25.0,
            },
            {
                "column": "Region",
                "missing_count": 2,
                "missing_percentage": 10.0,
            },
        ],
    }

    chart = select_chart(
        "missingness",
        result,
    )

    assert chart["chart_type"] == "missingness_bar"
    assert chart["title"] == "Missing Values by Column"
    assert chart["data"] == [
        {
            "column": "Merchant Number",
            "missing_percentage": 25.0,
        },
        {
            "column": "Region",
            "missing_percentage": 10.0,
        },
    ]


def test_unsupported_analysis_type_is_rejected():
    with pytest.raises(ValueError):
        select_chart(
            "unknown_analysis",
            {},
        )


def test_non_dictionary_result_is_rejected():
    with pytest.raises(TypeError):
        select_chart(
            "numeric_distribution",
            [1, 2, 3],
        )


def test_empty_numeric_result_is_handled():
    chart = select_chart(
        "numeric_distribution",
        {},
    )

    assert chart["chart_type"] == "histogram"
    assert chart["data"]["counts"] == []
    assert chart["data"]["edges"] == []


def test_empty_categorical_result_is_handled():
    chart = select_chart(
        "categorical_distribution",
        {},
    )

    assert chart["chart_type"] == "bar"
    assert chart["data"] == []


def test_empty_correlation_result_is_handled():
    chart = select_chart(
        "correlation",
        {},
    )

    assert chart["chart_type"] == "heatmap"
    assert chart["data"] == []


def test_empty_missingness_result_is_handled():
    chart = select_chart(
        "missingness",
        {},
    )

    assert chart["chart_type"] == "missingness_bar"
    assert chart["data"] == []


@pytest.mark.parametrize(
    "analysis_type",
    [
        "numeric_distribution",
        "categorical_distribution",
        "correlation",
        "missingness",
    ],
)
def test_chart_selection_does_not_modify_input(
    analysis_type,
):
    result = {
        "column": "Sales",
        "histogram_counts": [1, 2],
        "histogram_edges": [0, 5, 10],
        "categories": [
            {"category": "A", "count": 3},
        ],
        "method": "pearson",
        "pairs": [
            {
                "column_x": "A",
                "column_y": "B",
                "correlation": 0.5,
                "status": "assessed",
            },
        ],
        "columns": [
            {
                "column": "A",
                "missing_percentage": 20.0,
            },
        ],
    }

    original = copy.deepcopy(result)

    select_chart(
        analysis_type,
        result,
    )

    assert result == original
from copy import deepcopy


def test_time_series_selects_line_chart():
    result = {
        "column": "Date And Time Received",
        "frequency": "daily",
        "periods": [
            {"period": "2026-10-01T00:00:00", "count": 2},
            {"period": "2026-10-02T00:00:00", "count": 3},
        ],
    }

    chart = select_chart("time_series", result)

    assert chart["chart_type"] == "line"
    assert chart["title"] == "Daily Trend: Date And Time Received"
    assert chart["x_label"] == "Time"
    assert chart["y_label"] == "Count"
    assert chart["data"] == result["periods"]


def test_empty_time_series_chart():
    chart = select_chart(
        "time_series",
        {
            "column": "Date Received",
            "frequency": "monthly",
            "periods": [],
        },
    )

    assert chart["chart_type"] == "line"
    assert chart["data"] == []


def test_time_series_chart_does_not_modify_input():
    result = {
        "column": "Date Received",
        "frequency": "weekly",
        "periods": [
            {"period": "2026-10-05T00:00:00", "count": 4},
        ],
    }

    original = deepcopy(result)

    select_chart("time_series", result)

    assert result == original
