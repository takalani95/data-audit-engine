import pandas as pd

from src.profiling.profiler import (
    profile_dataset,
)
from src.quality.engine import (
    run_quality_audit,
)


def test_perfect_basic_dataset_scores_high():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
            ],
            "revenue": [
                100,
                200,
                300,
            ],
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    assert report.overall_score == 100.0
    assert report.status == "good"


def test_missing_values_reduce_completeness():
    dataframe = pd.DataFrame(
        {
            "value": [
                1,
                None,
                None,
                4,
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    assert (
        report
        .dimensions["completeness"]
        .score
        == 50.0
    )


def test_duplicate_rows_reduce_uniqueness():
    dataframe = pd.DataFrame(
        {
            "name": [
                "A",
                "A",
                "B",
            ],
            "value": [
                1,
                1,
                2,
            ],
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    assert (
        report
        .dimensions["uniqueness"]
        .score
        < 100
    )


def test_unnamed_columns_reduce_structure_score():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
            ],
            "Unnamed: 2": [
                1,
                2,
            ],
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    assert (
        report
        .dimensions[
            "structural_quality"
        ]
        .score
        < 100
    )


def test_quality_issues_are_explainable():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                None,
                "C",
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    missing_issues = [
        issue
        for issue in report.issues
        if issue.code == "MISSING_VALUES"
    ]

    assert len(missing_issues) == 1

    issue = missing_issues[0]

    assert issue.column == "customer"
    assert issue.affected_count == 1
    assert issue.affected_percentage > 0


def test_unimplemented_dimensions_are_not_assessed():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    report = run_quality_audit(
        dataframe,
        profile,
    )

    assert (
        report
        .dimensions["validity"]
        .assessed
        is False
    )

    assert (
        report
        .dimensions["validity"]
        .score
        is None
    )

    assert (
        report
        .dimensions["consistency"]
        .score
        is None
    )

    assert (
        report
        .dimensions["statistical_health"]
        .score
        is None
    )