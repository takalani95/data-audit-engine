
import copy

import plotly.graph_objects as go
import pytest

from src.visualization.plotly_renderer import render_chart


def test_histogram_returns_plotly_figure():
    spec = {
        "chart_type": "histogram",
        "title": "Sales Distribution",
        "x_label": "Sales",
        "y_label": "Frequency",
        "data": {
            "counts": [2, 5, 3],
            "edges": [0, 10, 20, 30],
        },
    }

    figure = render_chart(spec)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert isinstance(figure.data[0], go.Bar)
    assert list(figure.data[0].x) == [5, 15, 25]
    assert list(figure.data[0].y) == [2, 5, 3]
    assert list(figure.data[0].width) == [10, 10, 10]


def test_histogram_preserves_title_and_labels():
    spec = {
        "chart_type": "histogram",
        "title": "Revenue Distribution",
        "x_label": "Revenue",
        "y_label": "Count",
        "data": {
            "counts": [4],
            "edges": [0, 100],
        },
    }

    figure = render_chart(spec)

    assert figure.layout.title.text == "Revenue Distribution"
    assert figure.layout.xaxis.title.text == "Revenue"
    assert figure.layout.yaxis.title.text == "Count"


def test_histogram_rejects_incorrect_bin_edges():
    spec = {
        "chart_type": "histogram",
        "data": {
            "counts": [2, 3],
            "edges": [0, 10],
        },
    }

    with pytest.raises(ValueError, match="Histogram edges"):
        render_chart(spec)


def test_empty_histogram_returns_figure():
    spec = {
        "chart_type": "histogram",
        "data": {
            "counts": [],
            "edges": [],
        },
    }

    figure = render_chart(spec)

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 0


def test_categorical_bar_chart():
    spec = {
        "chart_type": "bar",
        "title": "Bank Frequencies",
        "data": [
            {"category": "FNB", "count": 12},
            {"category": "Capitec", "count": 8},
        ],
    }

    figure = render_chart(spec)

    assert isinstance(figure.data[0], go.Bar)
    assert list(figure.data[0].x) == ["FNB", "Capitec"]
    assert list(figure.data[0].y) == [12, 8]


def test_empty_categorical_bar_chart():
    figure = render_chart({
        "chart_type": "bar",
        "data": [],
    })

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 1
    assert len(figure.data[0].x) == 0


def test_missingness_bar_chart():
    spec = {
        "chart_type": "missingness_bar",
        "data": [
            {"column": "Region", "missing_percentage": 25.0},
            {"column": "Store", "missing_percentage": 10.0},
        ],
    }

    figure = render_chart(spec)

    assert isinstance(figure.data[0], go.Bar)
    assert list(figure.data[0].x) == ["Region", "Store"]
    assert list(figure.data[0].y) == [25.0, 10.0]


def test_heatmap_is_symmetric():
    spec = {
        "chart_type": "heatmap",
        "data": [
            {
                "column_x": "Sales",
                "column_y": "Revenue",
                "correlation": 0.8,
                "status": "assessed",
            },
        ],
    }

    figure = render_chart(spec)

    assert isinstance(figure.data[0], go.Heatmap)

    matrix = figure.data[0].z

    assert matrix.shape == (2, 2)
    assert matrix[0, 1] == pytest.approx(0.8)
    assert matrix[1, 0] == pytest.approx(0.8)


def test_heatmap_unassessed_pairs_remain_nan():
    spec = {
        "chart_type": "heatmap",
        "data": [
            {
                "column_x": "A",
                "column_y": "B",
                "correlation": None,
                "status": "insufficient_data",
            },
        ],
    }

    figure = render_chart(spec)
    matrix = figure.data[0].z

    assert matrix[0, 1] != matrix[0, 1]
    assert matrix[1, 0] != matrix[1, 0]


def test_heatmap_uses_fixed_correlation_scale():
    spec = {
        "chart_type": "heatmap",
        "data": [
            {
                "column_x": "A",
                "column_y": "B",
                "correlation": -0.5,
                "status": "assessed",
            },
        ],
    }

    figure = render_chart(spec)
    heatmap = figure.data[0]

    assert heatmap.zmin == -1
    assert heatmap.zmax == 1


def test_empty_heatmap_returns_figure():
    figure = render_chart({
        "chart_type": "heatmap",
        "data": [],
    })

    assert isinstance(figure, go.Figure)
    assert len(figure.data) == 0


def test_unsupported_chart_type_is_rejected():
    with pytest.raises(ValueError, match="Unsupported chart type"):
        render_chart({
            "chart_type": "pie",
            "data": [],
        })


def test_non_dictionary_specification_is_rejected():
    with pytest.raises(TypeError):
        render_chart(["histogram"])


@pytest.mark.parametrize(
    "chart_type,data",
    [
        (
            "histogram",
            {"counts": [2], "edges": [0, 10]},
        ),
        (
            "bar",
            [{"category": "A", "count": 2}],
        ),
        (
            "missingness_bar",
            [{"column": "A", "missing_percentage": 20.0}],
        ),
        (
            "heatmap",
            [{
                "column_x": "A",
                "column_y": "B",
                "correlation": 0.5,
                "status": "assessed",
            }],
        ),
    ],
)
def test_renderer_does_not_modify_input(chart_type, data):
    specification = {
        "chart_type": chart_type,
        "data": data,
    }

    original = copy.deepcopy(specification)

    render_chart(specification)

    assert specification == original
