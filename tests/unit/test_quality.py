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


def test_implemented_dimensions_are_assessed():
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

    implemented_dimensions = [
        "completeness",
        "uniqueness",
        "validity",
        "structural_quality",
    ]

    for dimension_name in implemented_dimensions:
        dimension = report.dimensions[
            dimension_name
        ]

        assert dimension.assessed is True
        assert dimension.score is not None


def test_pending_dimensions_are_not_assessed():
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

    pending_dimensions = [
        "consistency",
        "statistical_health",
    ]

    for dimension_name in pending_dimensions:
        dimension = report.dimensions[
            dimension_name
        ]

        assert dimension.assessed is False
        assert dimension.score is None


def test_validity_issue_flows_into_quality_report():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "",
                "C",
                "D",
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

    validity_dimension = report.dimensions[
        "validity"
    ]

    blank_issues = [
        issue
        for issue in validity_dimension.issues
        if issue.code == "BLANK_STRING"
    ]

    assert validity_dimension.assessed is True
    assert validity_dimension.score == 75.0

    assert len(blank_issues) == 1
    assert blank_issues[0].column == "customer"
    assert blank_issues[0].affected_count == 1


def test_validity_problem_reduces_overall_score():
    clean_dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
                "D",
            ]
        }
    )

    invalid_dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "",
                "C",
                "D",
            ]
        }
    )

    clean_profile = profile_dataset(
        clean_dataframe
    )

    invalid_profile = profile_dataset(
        invalid_dataframe
    )

    clean_report = run_quality_audit(
        clean_dataframe,
        clean_profile,
    )

    invalid_report = run_quality_audit(
        invalid_dataframe,
        invalid_profile,
    )

    assert (
        invalid_report
        .dimensions["validity"]
        .score
        <
        clean_report
        .dimensions["validity"]
        .score
    )

    assert (
        invalid_report.overall_score
        < clean_report.overall_score
    )