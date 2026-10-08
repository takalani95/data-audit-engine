
import numpy as np
import pandas as pd
import pytest

from src.visualization.distributions import (
    analyse_numeric_distribution,
    analyse_categorical_distribution,
)


def test_numeric_distribution_statistics():
    series = pd.Series(
        [10, 20, 30, 40, 50],
        name="Sales",
    )

    result = analyse_numeric_distribution(series)

    assert result["total_rows"] == 5
    assert result["valid_count"] == 5
    assert result["mean"] == 30.0
    assert result["median"] == 30.0
    assert result["min"] == 10.0
    assert result["max"] == 50.0
    assert result["q1"] == 20.0
    assert result["q3"] == 40.0


def test_numeric_distribution_missing_values():
    series = pd.Series(
        [10.0, np.nan, 30.0],
        name="Revenue",
    )

    result = analyse_numeric_distribution(series)

    assert result["total_rows"] == 3
    assert result["valid_count"] == 2
    assert result["missing_count"] == 1
    assert result["mean"] == 20.0


def test_numeric_distribution_infinity():
    series = pd.Series(
        [10.0, np.inf, -np.inf, 30.0],
        name="Amount",
    )

    result = analyse_numeric_distribution(series)

    assert result["non_finite_count"] == 2
    assert result["valid_count"] == 2
    assert result["mean"] == 20.0


def test_numeric_distribution_histogram():
    series = pd.Series(
        [1, 2, 3, 4, 5],
        name="Quantity",
    )

    result = analyse_numeric_distribution(
        series,
        bins=5,
    )

    assert len(result["histogram_counts"]) == 5
    assert len(result["histogram_edges"]) == 6
    assert sum(result["histogram_counts"]) == 5


def test_numeric_distribution_rejects_text():
    series = pd.Series(
        ["A", "B", "C"],
        name="Category",
    )

    with pytest.raises(TypeError):
        analyse_numeric_distribution(series)


def test_numeric_distribution_rejects_invalid_bins():
    series = pd.Series([1, 2, 3])

    with pytest.raises(ValueError):
        analyse_numeric_distribution(
            series,
            bins=0,
        )


def test_categorical_distribution_frequencies():
    series = pd.Series(
        ["FNB", "TJ", "FNB", "Capitec", "TJ", "FNB"],
        name="Bank",
    )

    result = analyse_categorical_distribution(series)

    assert result["total_rows"] == 6
    assert result["unique_count"] == 3
    assert result["categories"][0]["category"] == "FNB"
    assert result["categories"][0]["count"] == 3
    assert result["categories"][0]["percentage"] == 50.0


def test_categorical_distribution_missing_values():
    series = pd.Series(
        ["A", None, "A", "B"],
        name="Status",
    )

    result = analyse_categorical_distribution(series)

    assert result["missing_count"] == 1
    assert result["non_null_count"] == 3
    assert result["unique_count"] == 2


def test_categorical_distribution_top_n():
    series = pd.Series(
        ["A", "A", "B", "B", "C", "D"],
        name="Region",
    )

    result = analyse_categorical_distribution(
        series,
        top_n=2,
    )

    assert len(result["categories"]) == 2
    assert result["other_categories_count"] == 2


def test_categorical_distribution_rejects_invalid_top_n():
    series = pd.Series(["A", "B"])

    with pytest.raises(ValueError):
        analyse_categorical_distribution(
            series,
            top_n=0,
        )


def test_distribution_does_not_modify_source():
    series = pd.Series(
        [10.0, np.nan, 30.0],
        name="Sales",
    )

    original = series.copy(deep=True)

    analyse_numeric_distribution(series)

    pd.testing.assert_series_equal(
        series,
        original,
    )
