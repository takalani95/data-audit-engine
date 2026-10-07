import pandas as pd

from src.profiling.models import DatasetProfile
from src.quality.models import QualityIssue


def check_missing_values(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:

    issues: list[QualityIssue] = []

    for column in profile.column_profiles:

        if column.missing_count == 0:
            continue

        percentage = column.missing_percentage

        if percentage >= 50:
            severity = "critical"
        elif percentage >= 10:
            severity = "warning"
        else:
            severity = "info"

        issues.append(
            QualityIssue(
                code="MISSING_VALUES",
                category="completeness",
                severity=severity,
                title="Missing values detected",
                description=(
                    f"Column '{column.name}' contains "
                    f"{column.missing_count:,} missing values "
                    f"({percentage:.2f}%)."
                ),
                column=column.name,
                affected_count=column.missing_count,
                affected_percentage=percentage,
                evidence={
                    "missing_count":
                        column.missing_count,
                    "missing_percentage":
                        percentage,
                },
            )
        )

    return issues


def check_duplicate_rows(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:

    if profile.duplicate_rows == 0:
        return []

    percentage = profile.duplicate_percentage

    if percentage >= 10:
        severity = "critical"
    elif percentage >= 1:
        severity = "warning"
    else:
        severity = "info"

    return [
        QualityIssue(
            code="DUPLICATE_ROWS",
            category="uniqueness",
            severity=severity,
            title="Duplicate rows detected",
            description=(
                f"{profile.duplicate_rows:,} duplicate "
                f"rows were detected "
                f"({percentage:.2f}% of rows)."
            ),
            affected_count=profile.duplicate_rows,
            affected_percentage=percentage,
            evidence={
                "duplicate_rows":
                    profile.duplicate_rows,
                "duplicate_percentage":
                    percentage,
            },
        )
    ]


def check_unnamed_columns(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:

    if not profile.unnamed_columns:
        return []

    count = len(profile.unnamed_columns)

    percentage = (
        count / profile.columns * 100
        if profile.columns
        else 0
    )

    severity = (
        "critical"
        if percentage >= 50
        else "warning"
    )

    return [
        QualityIssue(
            code="UNNAMED_COLUMNS",
            category="structural_quality",
            severity=severity,
            title="Unnamed columns detected",
            description=(
                f"{count} column(s) have automatically "
                "generated names. This may indicate blank "
                "header cells or an incorrectly selected "
                "header row."
            ),
            affected_count=count,
            affected_percentage=round(
                percentage,
                2,
            ),
            evidence={
                "columns":
                    profile.unnamed_columns
            },
        )
    ]


def check_constant_columns(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:

    issues: list[QualityIssue] = []

    for column_name in profile.constant_columns:

        issues.append(
            QualityIssue(
                code="CONSTANT_COLUMN",
                category="structural_quality",
                severity="warning",
                title="Constant column detected",
                description=(
                    f"Column '{column_name}' contains "
                    "only one distinct non-null value."
                ),
                column=column_name,
                evidence={
                    "column": column_name
                },
            )
        )

    return issues


def check_high_missing_dataset(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> list[QualityIssue]:

    percentage = profile.missing_percentage

    if percentage < 20:
        return []

    severity = (
        "critical"
        if percentage >= 50
        else "warning"
    )

    return [
        QualityIssue(
            code="HIGH_DATASET_MISSINGNESS",
            category="completeness",
            severity=severity,
            title="High dataset missingness",
            description=(
                f"{percentage:.2f}% of all cells "
                "in the dataset are missing."
            ),
            affected_count=profile.missing_cells,
            affected_percentage=percentage,
            evidence={
                "missing_cells":
                    profile.missing_cells,
                "missing_percentage":
                    percentage,
            },
        )
    ]