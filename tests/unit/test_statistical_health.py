import pandas as pd

from src.statistics.statistical_health import (
    calculate_statistical_health_score,
    run_statistical_health_checks,
)


def test_iqr_outlier_is_detected():
    dataframe = pd.DataFrame(
        {
            "value": [
                10,
                11,
                10,
                12,
                11,
                10,
                12,
                11,
                10,
                1000,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    outlier_issues = [
        issue
        for issue in issues
        if issue.code
        == "NUMERIC_IQR_OUTLIERS"
    ]

    assert len(outlier_issues) == 1
    assert outlier_issues[0].column == "value"
    assert outlier_issues[0].affected_count == 1


def test_clean_numeric_distribution_has_no_outlier_issue():
    dataframe = pd.DataFrame(
        {
            "value": [
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    outlier_issues = [
        issue
        for issue in issues
        if issue.code
        == "NUMERIC_IQR_OUTLIERS"
    ]

    assert outlier_issues == []


def test_extreme_skewness_is_reported():
    dataframe = pd.DataFrame(
        {
            "value": [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                2,
                3,
                100,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    skew_issues = [
        issue
        for issue in issues
        if issue.code
        == "EXTREME_SKEWNESS"
    ]

    assert len(skew_issues) == 1
    assert skew_issues[0].severity == "info"


def test_skewness_does_not_reduce_score_by_itself():
    dataframe = pd.DataFrame(
        {
            "value": [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                2,
                3,
                100,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    skew_only_issues = [
        issue
        for issue in issues
        if issue.code
        == "EXTREME_SKEWNESS"
    ]

    score = calculate_statistical_health_score(
        dataframe,
        skew_only_issues,
    )

    assert score == 100.0


def test_outliers_reduce_statistical_health_score():
    dataframe = pd.DataFrame(
        {
            "value": [
                10,
                11,
                10,
                12,
                11,
                10,
                12,
                11,
                10,
                1000,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    score = calculate_statistical_health_score(
        dataframe,
        issues,
    )

    assert score < 100.0


def test_no_numeric_columns_returns_full_score():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    score = calculate_statistical_health_score(
        dataframe,
        issues,
    )

    assert score == 100.0


def test_small_numeric_sample_is_not_judged():
    dataframe = pd.DataFrame(
        {
            "value": [
                1,
                2,
                1000,
            ]
        }
    )

    issues = run_statistical_health_checks(
        dataframe
    )

    assert issues == []