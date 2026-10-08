
import pandas as pd
import pytest

from src.visualization.duration_charts import (
    create_duration_histogram,
)


def test_histogram_created():
    series = pd.Series(
        [0, "45 minutes", "1 hour 51 minutes"],
        name="Time To Attend",
    )

    fig = create_duration_histogram(series)

    assert fig.data[0].type == "histogram"
    assert len(fig.data[0].x) == 3
    assert fig.layout.xaxis.title.text == "Duration (minutes)"


def test_invalid_durations_excluded():
    series = pd.Series(
        ["1 hour", "unknown", None, "2 hours"],
        name="Time To Attend",
    )

    fig = create_duration_histogram(series)

    assert len(fig.data[0].x) == 2
    assert list(fig.data[0].x) == [60.0, 120.0]


def test_histogram_rejects_empty_durations():
    series = pd.Series(
        [None, "unknown"],
        name="Time To Attend",
    )

    with pytest.raises(ValueError):
        create_duration_histogram(series)


def test_histogram_rejects_invalid_bins():
    series = pd.Series(
        ["1 hour", "2 hours"],
        name="Time To Attend",
    )

    with pytest.raises(ValueError):
        create_duration_histogram(series, bins=1)


def test_histogram_does_not_modify_original_data():
    series = pd.Series(
        [0, "1 hour", None],
        name="Time To Attend",
    )

    original = series.copy(deep=True)

    create_duration_histogram(series)

    pd.testing.assert_series_equal(series, original)
