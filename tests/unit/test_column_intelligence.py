
import pandas as pd
import pytest

from src.visualization.column_intelligence import (
    analyse_column_intelligence,
)


def test_severity_levels_are_discrete_numeric():
    series = pd.Series(
        [1, 2, 3, 2, 1],
        name="Severity Level",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "discrete_numeric"
    assert result["recommended_chart"] == "bar"
    assert result["recommended_analysis"] == (
        "categorical_distribution"
    )


def test_continuous_measurements_use_histogram():
    series = pd.Series(
        [1.2, 2.5, 3.7, 4.1, 5.8],
        name="Resolution Time Minutes",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "continuous_numeric"
    assert result["recommended_chart"] == "histogram"


def test_native_datetime_column():
    series = pd.Series(
        pd.to_datetime(
            ["2026-10-01", "2026-10-02"]
        ),
        name="Date Received",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "datetime"
    assert result["recommended_chart"] == "line"


def test_date_strings_detected():
    series = pd.Series(
        [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
        ],
        name="Date And Time Received",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "datetime"
    assert result["recommended_analysis"] == "time_series"


def test_region_is_categorical():
    series = pd.Series(
        ["GN", "GS", "GN", "KZN"],
        name="Region",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "categorical"
    assert result["recommended_chart"] == "bar"


def test_identifier_is_not_treated_as_measurement():
    series = pd.Series(
        [10001, 10002, 10003],
        name="Merchant Number",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "identifier"
    assert result["recommended_chart"] is None


def test_boolean_column():
    series = pd.Series(
        [True, False, True],
        name="Within SLA",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "categorical"
    assert result["recommended_chart"] == "bar"


def test_all_missing_values():
    series = pd.Series(
        [None, None, None],
        name="Empty Column",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "unknown"
    assert result["valid_count"] == 0
    assert result["recommended_chart"] is None


def test_missing_values_are_counted():
    series = pd.Series(
        [1, 2, None, 3],
        name="Severity Level",
    )

    result = analyse_column_intelligence(series)

    assert result["total_count"] == 4
    assert result["valid_count"] == 3
    assert result["missing_count"] == 1


def test_invalid_input_rejected():
    with pytest.raises(TypeError):
        analyse_column_intelligence([1, 2, 3])


def test_invalid_max_categories_rejected():
    with pytest.raises(ValueError):
        analyse_column_intelligence(
            pd.Series([1, 2, 3]),
            max_categories=1,
        )


def test_original_series_not_modified():
    series = pd.Series(
        [1, 2, None, 3],
        name="Severity Level",
    )

    original = series.copy(deep=True)

    analyse_column_intelligence(series)

    pd.testing.assert_series_equal(
        series,
        original,
    )
def test_merchant_no_is_identifier():
    series = pd.Series(
        [568671, 502750, 100000001721850],
        name="Merchant No",
        dtype="object",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "identifier"
    assert result["recommended_chart"] is None



def test_time_to_attend_detected_as_duration():
    series = pd.Series(
        [
            0,
            "1 hour 51 minutes",
            "2 hours, 28 minutes",
            "6 hours",
            "45 minutes",
        ],
        name="Time To Attend",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "duration"
    assert result["recommended_chart"] == "histogram"
    assert result["recommended_analysis"] == (
        "duration_distribution"
    )


def test_duration_with_some_invalid_values():
    series = pd.Series(
        [
            "1 hour",
            "2 hours",
            "45 minutes",
            "3 hours",
            "unknown",
        ],
        name="Time To Attend",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "categorical"
    assert result["recommended_chart"] == "bar"


def test_non_duration_text_is_not_misclassified():
    series = pd.Series(
        ["Open", "Closed", "Pending"],
        name="Status",
    )

    result = analyse_column_intelligence(series)

    assert result["semantic_type"] == "categorical"
    assert result["recommended_chart"] == "bar"
