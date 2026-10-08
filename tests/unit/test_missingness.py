
import numpy as np
import pandas as pd
import pytest

from src.visualization.missingness import (
    analyse_missingness,
)


def test_complete_dataset_has_no_missing_values():
    dataframe = pd.DataFrame({
        "sales": [100, 200, 300],
        "region": ["GN", "GS", "GN"],
    })

    result = analyse_missingness(dataframe)

    assert result["total_rows"] == 3
    assert result["total_columns"] == 2
    assert result["total_cells"] == 6
    assert result["missing_cells"] == 0
    assert result["missing_percentage"] == 0.0
    assert result["complete_rows"] == 3
    assert result["incomplete_rows"] == 0


def test_column_missing_counts_and_percentages():
    dataframe = pd.DataFrame({
        "sales": [100, None, 300, None],
        "region": ["GN", "GS", None, "GN"],
    })

    result = analyse_missingness(dataframe)

    columns = {
        item["column"]: item
        for item in result["columns"]
    }

    assert columns["sales"]["missing_count"] == 2
    assert columns["sales"]["missing_percentage"] == 50.0
    assert columns["sales"]["non_missing_count"] == 2

    assert columns["region"]["missing_count"] == 1
    assert columns["region"]["missing_percentage"] == 25.0


def test_overall_missing_percentage():
    dataframe = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": [None, 2, 3, 4],
    })

    result = analyse_missingness(dataframe)

    assert result["total_cells"] == 8
    assert result["missing_cells"] == 3
    assert result["missing_percentage"] == 37.5


def test_incomplete_row_counts():
    dataframe = pd.DataFrame({
        "a": [1, None, 3, None],
        "b": [2, 2, None, None],
    })

    result = analyse_missingness(dataframe)

    assert result["complete_rows"] == 1
    assert result["incomplete_rows"] == 3
    assert result["incomplete_row_percentage"] == 75.0


def test_row_missingness_distribution():
    dataframe = pd.DataFrame({
        "a": [1, None, None],
        "b": [2, 3, None],
    })

    result = analyse_missingness(dataframe)

    assert result["row_distribution"] == [
        {"missing_columns": 0, "row_count": 1},
        {"missing_columns": 1, "row_count": 1},
        {"missing_columns": 2, "row_count": 1},
    ]


def test_missingness_patterns():
    dataframe = pd.DataFrame({
        "a": [1, None, None, 4],
        "b": [2, 2, None, 5],
        "c": [3, 3, 3, 6],
    })

    result = analyse_missingness(dataframe)

    patterns = {
        tuple(item["missing_columns"]): item["row_count"]
        for item in result["patterns"]
    }

    assert patterns[()] == 2
    assert patterns[("a",)] == 1
    assert patterns[("a", "b")] == 1


def test_top_n_patterns_limits_results():
    dataframe = pd.DataFrame({
        "a": [1, None, None],
        "b": [2, 2, None],
    })

    result = analyse_missingness(
        dataframe,
        top_n_patterns=2,
    )

    assert len(result["patterns"]) == 2


def test_invalid_top_n_patterns_is_rejected():
    dataframe = pd.DataFrame({
        "a": [1, None],
    })

    with pytest.raises(ValueError):
        analyse_missingness(
            dataframe,
            top_n_patterns=0,
        )


def test_empty_dataframe():
    dataframe = pd.DataFrame({
        "a": pd.Series(dtype=float),
        "b": pd.Series(dtype="string"),
    })

    result = analyse_missingness(dataframe)

    assert result["total_rows"] == 0
    assert result["total_columns"] == 2
    assert result["total_cells"] == 0
    assert result["missing_cells"] == 0
    assert result["complete_rows"] == 0
    assert result["incomplete_rows"] == 0
    assert result["patterns"] == []


def test_zero_column_dataframe():
    dataframe = pd.DataFrame(index=range(3))

    result = analyse_missingness(dataframe)

    assert result["total_rows"] == 3
    assert result["total_columns"] == 0
    assert result["total_cells"] == 0
    assert result["missing_cells"] == 0
    assert result["complete_rows"] == 3
    assert result["incomplete_rows"] == 0


def test_blank_strings_are_not_missing():
    dataframe = pd.DataFrame({
        "status": ["", " ", None, "Open"],
    })

    result = analyse_missingness(dataframe)

    assert result["missing_cells"] == 1
    assert result["columns"][0]["missing_count"] == 1


def test_different_pandas_missing_types():
    dataframe = pd.DataFrame({
        "a": [None, np.nan, pd.NA, 10],
    })

    result = analyse_missingness(dataframe)

    assert result["missing_cells"] == 3
    assert result["missing_percentage"] == 75.0


def test_duplicate_column_names_are_rejected():
    dataframe = pd.DataFrame(
        [[1, 2], [3, 4]],
        columns=["a", "a"],
    )

    with pytest.raises(ValueError):
        analyse_missingness(dataframe)


def test_original_dataframe_is_not_modified():
    dataframe = pd.DataFrame({
        "a": [1.0, np.nan, 3.0],
        "b": ["GN", None, "GS"],
    })

    original = dataframe.copy(deep=True)

    analyse_missingness(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )
