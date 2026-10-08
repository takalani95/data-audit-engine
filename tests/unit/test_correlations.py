
import numpy as np
import pandas as pd
import pytest

from src.visualization.correlations import (
    analyse_correlations,
)


def test_perfect_positive_pearson_correlation():
    dataframe = pd.DataFrame({
        "sales": [1, 2, 3, 4, 5, 6, 7, 8],
        "revenue": [10, 20, 30, 40, 50, 60, 70, 80],
    })

    result = analyse_correlations(dataframe)

    assert result["method"] == "pearson"
    assert result["assessed_pairs"] == 1
    assert result["pairs"][0]["status"] == "assessed"
    assert result["pairs"][0]["correlation"] == pytest.approx(1.0)


def test_perfect_negative_pearson_correlation():
    dataframe = pd.DataFrame({
        "x": list(range(1, 9)),
        "y": list(range(8, 0, -1)),
    })

    result = analyse_correlations(dataframe)

    assert result["pairs"][0]["correlation"] == pytest.approx(-1.0)


def test_spearman_monotonic_relationship():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [1, 4, 9, 16, 25, 36, 49, 64],
    })

    result = analyse_correlations(
        dataframe,
        method="spearman",
    )

    assert result["pairs"][0]["correlation"] == pytest.approx(1.0)


def test_insufficient_paired_observations():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [1, 2, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
    })

    result = analyse_correlations(dataframe)

    assert result["assessed_pairs"] == 0
    assert result["unassessed_pairs"] == 1
    assert result["pairs"][0]["paired_count"] == 2
    assert result["pairs"][0]["correlation"] is None
    assert result["pairs"][0]["status"] == "insufficient_data"


def test_constant_column_is_not_assessed():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "constant": [10] * 8,
    })

    result = analyse_correlations(dataframe)

    assert result["pairs"][0]["status"] == "constant_column"
    assert result["pairs"][0]["correlation"] is None


def test_infinite_values_are_excluded():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y": [2, 4, 6, 8, 10, 12, 14, 16, np.inf, -np.inf],
    })

    result = analyse_correlations(dataframe)

    assert result["pairs"][0]["paired_count"] == 8
    assert result["pairs"][0]["status"] == "assessed"
    assert result["pairs"][0]["correlation"] == pytest.approx(1.0)


def test_boolean_columns_are_excluded():
    dataframe = pd.DataFrame({
        "x": list(range(8)),
        "y": list(range(8)),
        "flag": [True, False] * 4,
    })

    result = analyse_correlations(dataframe)

    assert result["numeric_columns"] == ["x", "y"]
    assert len(result["pairs"]) == 1


def test_identifier_can_be_explicitly_excluded():
    dataframe = pd.DataFrame({
        "customer_id": list(range(100, 108)),
        "sales": list(range(8)),
        "revenue": [value * 5 for value in range(8)],
    })

    result = analyse_correlations(
        dataframe,
        excluded_columns=["customer_id"],
    )

    assert result["numeric_columns"] == ["sales", "revenue"]
    assert len(result["pairs"]) == 1


def test_text_columns_are_excluded():
    dataframe = pd.DataFrame({
        "x": list(range(8)),
        "y": list(range(8)),
        "region": ["North", "South"] * 4,
    })

    result = analyse_correlations(dataframe)

    assert "region" not in result["numeric_columns"]


def test_invalid_method_is_rejected():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3],
        "y": [4, 5, 6],
    })

    with pytest.raises(ValueError):
        analyse_correlations(
            dataframe,
            method="invalid",
        )


def test_invalid_min_pairs_is_rejected():
    dataframe = pd.DataFrame({
        "x": [1, 2, 3],
        "y": [4, 5, 6],
    })

    with pytest.raises(ValueError):
        analyse_correlations(
            dataframe,
            min_pairs=2,
        )


def test_no_numeric_columns():
    dataframe = pd.DataFrame({
        "region": ["A", "B", "C"],
        "status": ["Open", "Closed", "Open"],
    })

    result = analyse_correlations(dataframe)

    assert result["numeric_columns"] == []
    assert result["pairs"] == []
    assert result["assessed_pairs"] == 0


def test_duplicate_column_names_are_rejected():
    dataframe = pd.DataFrame(
        [[1, 2], [3, 4]],
        columns=["x", "x"],
    )

    with pytest.raises(ValueError):
        analyse_correlations(dataframe)


def test_source_dataframe_is_not_modified():
    dataframe = pd.DataFrame({
        "x": [1.0, 2.0, np.inf, 4.0],
        "y": [2.0, 4.0, 6.0, 8.0],
    })

    original = dataframe.copy(deep=True)

    analyse_correlations(
        dataframe,
        min_pairs=3,
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )
