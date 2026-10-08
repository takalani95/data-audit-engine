
from datetime import timedelta

import pandas as pd
import pytest

from src.visualization.duration_intelligence import (
    analyse_duration_column,
    parse_duration_minutes,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, 0.0),
        (45, 45.0),
        ("0", 0.0),
        ("45 minutes", 45.0),
        ("1 hour 51 minutes", 111.0),
        ("1 hour, 58 minutes", 118.0),
        ("2 hours, 28 minutes", 148.0),
        ("6 hours ", 360.0),
        ("1 day 2 hours", 1560.0),
        ("30 seconds", 0.5),
        (timedelta(hours=2), 120.0),
        (pd.Timedelta(minutes=90), 90.0),
    ],
)
def test_valid_durations(value, expected):
    assert parse_duration_minutes(value) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "unknown",
        "not attended",
        "-5",
        "-2 hours",
        True,
        False,
        float("inf"),
        float("-inf"),
    ],
)
def test_invalid_durations(value):
    assert parse_duration_minutes(value) is None


def test_duration_column_summary():
    series = pd.Series(
        [
            0,
            "1 hour 51 minutes",
            "2 hours, 28 minutes",
            None,
            "unknown",
        ],
        name="Time To Attend",
    )

    result = analyse_duration_column(series)

    assert result["total_count"] == 5
    assert result["valid_count"] == 3
    assert result["invalid_or_missing_count"] == 2
    assert result["unit"] == "minutes"
    assert result["values"] == [0.0, 111.0, 148.0]
    assert result["median"] == 111.0


def test_empty_duration_column():
    result = analyse_duration_column(
        pd.Series([], dtype="object")
    )

    assert result["total_count"] == 0
    assert result["valid_count"] == 0
    assert result["mean"] is None


def test_duration_analysis_does_not_modify_source():
    series = pd.Series(
        [0, "2 hours", None],
        name="Time To Attend",
    )

    original = series.copy(deep=True)

    analyse_duration_column(series)

    pd.testing.assert_series_equal(series, original)


def test_duration_analysis_rejects_invalid_input():
    with pytest.raises(TypeError):
        analyse_duration_column(["1 hour", "2 hours"])
