import numpy as np
import pandas as pd

from src.profiling.profiler import (
    profile_dataset,
)
from src.quality.validity import (
    calculate_validity_score,
    run_validity_checks,
)


def test_blank_strings_are_detected():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "",
                "   ",
                "D",
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    blank_issues = [
        issue
        for issue in issues
        if issue.code == "BLANK_STRING"
    ]

    assert len(blank_issues) == 1
    assert blank_issues[0].affected_count == 2
    assert blank_issues[0].affected_percentage == 50.0


def test_infinite_values_are_detected():
    dataframe = pd.DataFrame(
        {
            "amount": [
                100.0,
                np.inf,
                300.0,
                -np.inf,
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    infinite_issues = [
        issue
        for issue in issues
        if issue.code == "INFINITE_VALUE"
    ]

    assert len(infinite_issues) == 1
    assert infinite_issues[0].affected_count == 2


def test_mixed_types_are_reported():
    dataframe = pd.DataFrame(
        {
            "Time To Attend": [
                "1 hour 51 minutes",
                45,
                "35 minutes",
                60,
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    mixed_issues = [
        issue
        for issue in issues
        if issue.code == "MIXED_PYTHON_TYPES"
    ]

    assert len(mixed_issues) == 1
    assert mixed_issues[0].severity == "info"


def test_mixed_types_do_not_automatically_reduce_validity():
    dataframe = pd.DataFrame(
        {
            "Time To Attend": [
                "1 hour 51 minutes",
                45,
                "35 minutes",
                60,
            ]
        }
    )

    profile = profile_dataset(
        dataframe
    )

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    score = calculate_validity_score(
        dataframe,
        issues,
    )

    assert score == 100.0


def test_blank_values_reduce_validity_score():
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

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    score = calculate_validity_score(
        dataframe,
        issues,
    )

    assert score == 75.0


def test_clean_dataset_has_full_validity_score():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
            ],
            "amount": [
                100,
                200,
                300,
            ],
        }
    )

    profile = profile_dataset(
        dataframe
    )

    issues = run_validity_checks(
        dataframe,
        profile,
    )

    score = calculate_validity_score(
        dataframe,
        issues,
    )

    assert score == 100.0