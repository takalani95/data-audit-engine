import pandas as pd

from src.quality.consistency import (
    calculate_consistency_score,
    run_consistency_checks,
)


def test_surrounding_whitespace_is_detected():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                " FNB",
                "ABSA ",
                "Nedbank",
            ]
        }
    )

    issues = run_consistency_checks(
        dataframe
    )

    whitespace_issues = [
        issue
        for issue in issues
        if issue.code
        == "SURROUNDING_WHITESPACE"
    ]

    assert len(whitespace_issues) == 1
    assert whitespace_issues[0].affected_count == 2
    assert (
        whitespace_issues[0]
        .affected_percentage
        == 50.0
    )


def test_case_variants_are_detected():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                "FNB",
                "fnb",
                "Fnb",
            ]
        }
    )

    issues = run_consistency_checks(
        dataframe
    )

    variant_issues = [
        issue
        for issue in issues
        if issue.code
        == "TEXT_REPRESENTATION_VARIANTS"
    ]

    assert len(variant_issues) == 1
    assert (
        variant_issues[0]
        .affected_count
        == 2
    )


def test_clean_categories_have_no_consistency_issue():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                "ABSA",
                "Nedbank",
                "Capitec",
            ]
        }
    )

    issues = run_consistency_checks(
        dataframe
    )

    assert issues == []


def test_consistency_checks_do_not_modify_dataframe():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                " fnb ",
            ]
        }
    )

    original = dataframe.copy(
        deep=True
    )

    run_consistency_checks(
        dataframe
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_consistency_problem_reduces_score():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                "FNB",
                "fnb",
                "ABSA",
            ]
        }
    )

    issues = run_consistency_checks(
        dataframe
    )

    score = calculate_consistency_score(
        dataframe,
        issues,
    )

    assert score < 100.0


def test_clean_dataset_has_full_consistency_score():
    dataframe = pd.DataFrame(
        {
            "bank": [
                "FNB",
                "ABSA",
                "Nedbank",
            ],
            "region": [
                "Gauteng",
                "Limpopo",
                "Western Cape",
            ],
        }
    )

    issues = run_consistency_checks(
        dataframe
    )

    score = calculate_consistency_score(
        dataframe,
        issues,
    )

    assert score == 100.0