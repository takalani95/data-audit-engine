from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from src.profiling.models import DatasetProfile
from src.quality.models import QualityIssue


def _severity_from_percentage(
    percentage: float,
) -> str:
    """
    Convert an affected percentage into an issue severity.
    """

    if percentage >= 20:
        return "critical"

    if percentage >= 5:
        return "warning"

    return "info"


def _percentage(
    affected_count: int,
    denominator: int,
) -> float:
    """
    Safely calculate a percentage.
    """

    if denominator <= 0:
        return 0.0

    return round(
        affected_count / denominator * 100,
        2,
    )


def _is_blank_string(
    value: Any,
) -> bool:
    """
    Return True when a value is a string containing
    only whitespace.
    """

    return (
        isinstance(value, str)
        and value.strip() == ""
    )


def check_blank_strings(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect strings that are technically non-null but
    contain no meaningful content.
    """

    issues: list[QualityIssue] = []

    for column_name in dataframe.columns:

        series = dataframe[column_name]

        blank_mask = series.map(
            _is_blank_string
        )

        affected_count = int(
            blank_mask.sum()
        )

        if affected_count == 0:
            continue

        non_null_count = int(
            series.notna().sum()
        )

        affected_percentage = _percentage(
            affected_count,
            non_null_count,
        )

        issues.append(
            QualityIssue(
                code="BLANK_STRING",
                category="validity",
                severity=_severity_from_percentage(
                    affected_percentage
                ),
                title="Blank string values detected",
                description=(
                    f"Column '{column_name}' contains "
                    f"{affected_count:,} blank or "
                    "whitespace-only value(s) "
                    f"({affected_percentage:.2f}% of "
                    "non-null values)."
                ),
                column=str(column_name),
                affected_count=affected_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "blank_count":
                        affected_count,
                    "affected_percentage":
                        affected_percentage,
                },
            )
        )

    return issues


def check_infinite_numeric_values(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect positive or negative infinity in numeric
    columns.
    """

    issues: list[QualityIssue] = []

    numeric_columns = dataframe.select_dtypes(
        include=["number"]
    ).columns

    for column_name in numeric_columns:

        series = dataframe[column_name]

        infinity_mask = series.map(
            lambda value: (
                isinstance(
                    value,
                    (int, float, np.integer, np.floating),
                )
                and not pd.isna(value)
                and math.isinf(float(value))
            )
        )

        affected_count = int(
            infinity_mask.sum()
        )

        if affected_count == 0:
            continue

        non_null_count = int(
            series.notna().sum()
        )

        affected_percentage = _percentage(
            affected_count,
            non_null_count,
        )

        issues.append(
            QualityIssue(
                code="INFINITE_VALUE",
                category="validity",
                severity=_severity_from_percentage(
                    affected_percentage
                ),
                title="Infinite numeric values detected",
                description=(
                    f"Column '{column_name}' contains "
                    f"{affected_count:,} infinite numeric "
                    f"value(s) ({affected_percentage:.2f}% "
                    "of non-null values)."
                ),
                column=str(column_name),
                affected_count=affected_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "infinite_count":
                        affected_count,
                    "affected_percentage":
                        affected_percentage,
                },
            )
        )

    return issues


def check_mixed_python_types(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:
    """
    Detect object columns containing materially mixed
    Python value types.

    This is intentionally conservative. Mixed types are
    reported for review rather than automatically treated
    as invalid values.
    """

    issues: list[QualityIssue] = []

    profile_by_name = {
        column.name: column
        for column in profile.column_profiles
    }

    for column_name in dataframe.columns:

        series = dataframe[column_name]

        if series.dtype != "object":
            continue

        non_null = series.dropna()

        if non_null.empty:
            continue

        type_counts = (
            non_null
            .map(lambda value: type(value).__name__)
            .value_counts()
        )

        if len(type_counts) <= 1:
            continue

        dominant_count = int(
            type_counts.iloc[0]
        )

        minority_count = int(
            len(non_null) - dominant_count
        )

        affected_percentage = _percentage(
            minority_count,
            len(non_null),
        )

        semantic_type = (
            profile_by_name[
                str(column_name)
            ].semantic_type
            if str(column_name) in profile_by_name
            else "unknown"
        )

        issues.append(
            QualityIssue(
                code="MIXED_PYTHON_TYPES",
                category="validity",
                severity="info",
                title="Mixed value types detected",
                description=(
                    f"Column '{column_name}' contains "
                    "multiple underlying Python value "
                    "types. This may be legitimate, but "
                    "should be reviewed before modelling "
                    "or strict type conversion."
                ),
                column=str(column_name),
                affected_count=minority_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "python_types":
                        type_counts.to_dict(),
                    "semantic_type":
                        semantic_type,
                    "minority_count":
                        minority_count,
                },
            )
        )

    return issues


def run_validity_checks(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:
    """
    Run all currently implemented validity checks.
    """

    issues: list[QualityIssue] = []

    issues.extend(
        check_blank_strings(
            dataframe
        )
    )

    issues.extend(
        check_infinite_numeric_values(
            dataframe
        )
    )

    issues.extend(
        check_mixed_python_types(
            dataframe,
            profile,
        )
    )

    return issues


def calculate_validity_score(
    dataframe: pd.DataFrame,
    issues: list[QualityIssue],
) -> float:
    """
    Calculate an explainable validity score.

    Only objectively invalid values currently contribute
    to score deductions.

    Informational findings such as mixed Python types do
    not reduce the score.
    """

    total_cells = int(
        dataframe.shape[0]
        * dataframe.shape[1]
    )

    if total_cells == 0:
        return 100.0

    invalid_codes = {
        "BLANK_STRING",
        "INFINITE_VALUE",
    }

    invalid_count = sum(
        issue.affected_count
        for issue in issues
        if issue.code in invalid_codes
    )

    invalid_percentage = (
        invalid_count
        / total_cells
        * 100
    )

    return round(
        max(
            0.0,
            100.0 - invalid_percentage,
        ),
        2,
    )