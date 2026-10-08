
import pandas as pd
import pytest

from src.visualization.dataset_intelligence import (
    analyse_dataset_intelligence,
)


def make_sample_dataframe():
    return pd.DataFrame({
        "Case No": [10001, 10002, 10003, 10004],
        "Severity Level": [1, 2, 3, 2],
        "Region": ["GN", "GS", "GN", "KZN"],
        "Resolution Minutes": [15.5, 40.2, 60.7, 120.4],
        "Date Received": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04",
        ],
    })


def test_dataset_dimensions():
    result = analyse_dataset_intelligence(
        make_sample_dataframe()
    )

    assert result["row_count"] == 4
    assert result["column_count"] == 5


def test_recommendation_counts():
    result = analyse_dataset_intelligence(
        make_sample_dataframe()
    )

    assert result["recommended_count"] == 4
    assert result["skipped_count"] == 1


def test_chart_counts():
    result = analyse_dataset_intelligence(
        make_sample_dataframe()
    )

    assert result["chart_counts"] == {
        "bar": 2,
        "histogram": 1,
        "line": 1,
    }


def test_identifier_is_skipped():
    result = analyse_dataset_intelligence(
        make_sample_dataframe()
    )

    skipped = result["skipped"]

    assert len(skipped) == 1
    assert skipped[0]["column"] == "Case No"
    assert skipped[0]["semantic_type"] == "identifier"


def test_column_order_is_preserved():
    dataframe = make_sample_dataframe()

    result = analyse_dataset_intelligence(dataframe)

    actual = [
        item["column"]
        for item in result["columns"]
    ]

    assert actual == list(dataframe.columns)


def test_empty_dataframe():
    dataframe = pd.DataFrame()

    result = analyse_dataset_intelligence(dataframe)

    assert result["row_count"] == 0
    assert result["column_count"] == 0
    assert result["recommended_count"] == 0
    assert result["skipped_count"] == 0
    assert result["chart_counts"] == {}


def test_all_missing_column_is_skipped():
    dataframe = pd.DataFrame({
        "Empty": [None, None, None],
        "Region": ["GN", "GS", "GN"],
    })

    result = analyse_dataset_intelligence(dataframe)

    assert result["recommended_count"] == 1
    assert result["skipped_count"] == 1


def test_duplicate_column_names():
    dataframe = pd.DataFrame(
        [
            [1, "GN"],
            [2, "GS"],
            [3, "KZN"],
        ],
        columns=["Region", "Region"],
    )

    result = analyse_dataset_intelligence(dataframe)

    assert result["column_count"] == 2
    assert len(result["columns"]) == 2
    assert result["columns"][0]["column_index"] == 0
    assert result["columns"][1]["column_index"] == 1


def test_original_dataframe_not_modified():
    dataframe = make_sample_dataframe()
    original = dataframe.copy(deep=True)

    analyse_dataset_intelligence(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_invalid_input():
    with pytest.raises(TypeError):
        analyse_dataset_intelligence(
            {"Region": ["GN", "GS"]}
        )


def test_invalid_max_categories():
    with pytest.raises(ValueError):
        analyse_dataset_intelligence(
            make_sample_dataframe(),
            max_categories=1,
        )


def test_recommendations_contain_explanations():
    result = analyse_dataset_intelligence(
        make_sample_dataframe()
    )

    for item in result["columns"]:
        assert isinstance(item["reason"], str)
        assert item["reason"]
