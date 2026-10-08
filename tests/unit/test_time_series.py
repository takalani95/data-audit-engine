
import pandas as pd
import pytest

from src.visualization.time_series import analyse_time_series


def test_daily_aggregation():
    series = pd.Series(
        [
            "2026-10-01 08:30",
            "2026-10-01 10:15",
            "2026-10-02 09:00",
        ],
        name="Date Received",
    )

    result = analyse_time_series(series, "daily")

    assert result["frequency"] == "daily"
    assert result["total_rows"] == 3
    assert result["valid_count"] == 3
    assert result["periods"] == [
        {"period": "2026-10-01T00:00:00", "count": 2},
        {"period": "2026-10-02T00:00:00", "count": 1},
    ]


def test_weekly_aggregation_starts_monday():
    series = pd.Series(
        [
            "2026-10-04",
            "2026-10-05",
            "2026-10-06",
        ]
    )

    result = analyse_time_series(series, "weekly")

    assert result["periods"] == [
        {"period": "2026-09-28T00:00:00", "count": 1},
        {"period": "2026-10-05T00:00:00", "count": 2},
    ]


def test_monthly_aggregation():
    series = pd.Series(
        [
            "2026-09-15",
            "2026-10-01",
            "2026-10-20",
        ]
    )

    result = analyse_time_series(series, "monthly")

    assert result["periods"] == [
        {"period": "2026-09-01T00:00:00", "count": 1},
        {"period": "2026-10-01T00:00:00", "count": 2},
    ]


def test_hourly_aggregation():
    series = pd.Series(
        [
            "2026-10-01 08:10",
            "2026-10-01 08:45",
            "2026-10-01 09:05",
        ]
    )

    result = analyse_time_series(series, "hourly")

    assert result["periods"] == [
        {"period": "2026-10-01T08:00:00", "count": 2},
        {"period": "2026-10-01T09:00:00", "count": 1},
    ]


def test_missing_and_invalid_dates():
    series = pd.Series(
        [
            "2026-10-01",
            None,
            "not-a-date",
        ]
    )

    result = analyse_time_series(series)

    assert result["total_rows"] == 3
    assert result["valid_count"] == 1
    assert result["missing_or_invalid_count"] == 2


def test_empty_series():
    result = analyse_time_series(
        pd.Series([], dtype="object")
    )

    assert result["total_rows"] == 0
    assert result["valid_count"] == 0
    assert result["periods"] == []
    assert result["start_date"] is None
    assert result["end_date"] is None


def test_all_invalid_dates():
    result = analyse_time_series(
        pd.Series(["invalid", None])
    )

    assert result["valid_count"] == 0
    assert result["missing_or_invalid_count"] == 2
    assert result["periods"] == []


def test_invalid_frequency_rejected():
    with pytest.raises(ValueError):
        analyse_time_series(
            pd.Series(["2026-10-01"]),
            frequency="yearly",
        )


def test_non_series_input_rejected():
    with pytest.raises(TypeError):
        analyse_time_series(
            ["2026-10-01"]
        )


def test_source_series_not_modified():
    series = pd.Series(
        [
            "2026-10-01",
            "invalid",
            None,
        ]
    )

    original = series.copy(deep=True)

    analyse_time_series(series)

    pd.testing.assert_series_equal(
        series,
        original,
    )


def test_chronological_ordering():
    series = pd.Series(
        [
            "2026-10-03",
            "2026-10-01",
            "2026-10-02",
        ]
    )

    result = analyse_time_series(series)

    periods = [
        item["period"]
        for item in result["periods"]
    ]

    assert periods == sorted(periods)


def test_timezone_aware_dates():
    series = pd.Series(
        pd.to_datetime(
            [
                "2026-10-01 08:00",
                "2026-10-01 09:00",
            ]
        ).tz_localize("Africa/Johannesburg")
    )

    result = analyse_time_series(series, "daily")

    assert result["valid_count"] == 2
    assert result["periods"][0]["count"] == 2
    assert result["periods"][0]["period"] == (
        "2026-10-01T00:00:00"
    )
