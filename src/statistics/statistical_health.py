from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.quality.models import QualityIssue


MINIMUM_SAMPLE_SIZE = 8
OUTLIER_IQR_MULTIPLIER = 1.5
EXTREME_SKEW_THRESHOLD = 2.0


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


def _finite_numeric_values(
    series: pd.Series,
) -> pd.Series:
    """
    Return finite, non-null numeric values.

    Infinite values belong to the validity dimension and
    are excluded from statistical-health calculations.
    """

    numeric = pd.to_numeric(
        series,
        errors="coerce",
    )

    numeric = numeric.dropna()

    if numeric.empty:
        return numeric

    finite_mask = np.isfinite(
        numeric.astype(float)
    )

    return numeric[
        finite_mask
    ]


def check_iqr_outliers(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect numeric observations outside the standard
    1.5 * IQR fences.

    Outliers are statistical observations rather than
    automatically invalid values, so findings are
    informational or warnings rather than critical.
    """

    issues: list[QualityIssue] = []

    numeric_columns = dataframe.select_dtypes(
        include=["number"]
    ).columns

    for column_name in numeric_columns:

        values = _finite_numeric_values(
            dataframe[column_name]
        )

        if len(values) < MINIMUM_SAMPLE_SIZE:
            continue

        q1 = float(
            values.quantile(0.25)
        )

        q3 = float(
            values.quantile(0.75)
        )

        iqr = q3 - q1

        if not math.isfinite(iqr):
            continue

        if iqr <= 0:
            continue

        lower_bound = (
            q1
            - OUTLIER_IQR_MULTIPLIER * iqr
        )

        upper_bound = (
            q3
            + OUTLIER_IQR_MULTIPLIER * iqr
        )

        outlier_mask = (
            (values < lower_bound)
            | (values > upper_bound)
        )

        affected_count = int(
            outlier_mask.sum()
        )

        if affected_count == 0:
            continue

        affected_percentage = _percentage(
            affected_count,
            len(values),
        )

        severity = (
            "warning"
            if affected_percentage >= 10
            else "info"
        )

        examples = (
            values[outlier_mask]
            .head(5)
            .tolist()
        )

        issues.append(
            QualityIssue(
                code="NUMERIC_IQR_OUTLIERS",
                category="statistical_health",
                severity=severity,
                title="Numeric outliers detected",
                description=(
                    f"Column '{column_name}' contains "
                    f"{affected_count:,} value(s) outside "
                    "the standard 1.5 × IQR range "
                    f"({affected_percentage:.2f}% of "
                    "finite numeric values)."
                ),
                column=str(column_name),
                affected_count=affected_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "lower_bound":
                        lower_bound,
                    "upper_bound":
                        upper_bound,
                    "examples":
                        examples,
                },
            )
        )

    return issues


def check_extreme_skewness(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect strongly skewed numeric distributions.

    Skewness is not inherently a data-quality defect.
    Findings are therefore informational and do not
    automatically reduce the statistical-health score.
    """

    issues: list[QualityIssue] = []

    numeric_columns = dataframe.select_dtypes(
        include=["number"]
    ).columns

    for column_name in numeric_columns:

        values = _finite_numeric_values(
            dataframe[column_name]
        )

        if len(values) < MINIMUM_SAMPLE_SIZE:
            continue

        if values.nunique() <= 1:
            continue

        skewness = float(
            values.skew()
        )

        if not math.isfinite(skewness):
            continue

        if abs(skewness) < EXTREME_SKEW_THRESHOLD:
            continue

        issues.append(
            QualityIssue(
                code="EXTREME_SKEWNESS",
                category="statistical_health",
                severity="info",
                title="Highly skewed distribution detected",
                description=(
                    f"Column '{column_name}' has a "
                    f"skewness of {skewness:.2f}. "
                    "This may be legitimate, but should "
                    "be considered during analysis or "
                    "model preparation."
                ),
                column=str(column_name),
                affected_count=0,
                affected_percentage=0.0,
                evidence={
                    "skewness":
                        round(skewness, 4),
                    "threshold":
                        EXTREME_SKEW_THRESHOLD,
                    "sample_size":
                        int(len(values)),
                },
            )
        )

    return issues


def run_statistical_health_checks(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Run all currently implemented statistical-health
    checks.
    """

    issues: list[QualityIssue] = []

    issues.extend(
        check_iqr_outliers(
            dataframe
        )
    )

    issues.extend(
        check_extreme_skewness(
            dataframe
        )
    )

    return issues


def calculate_statistical_health_score(
    dataframe: pd.DataFrame,
    issues: list[QualityIssue],
) -> float:
    """
    Calculate an explainable statistical-health score.

    Only IQR outlier findings currently reduce the score.

    Extreme skewness remains informational because a
    skewed distribution may be perfectly legitimate.
    """

    numeric_columns = dataframe.select_dtypes(
        include=["number"]
    ).columns

    total_numeric_cells = 0

    for column_name in numeric_columns:

        values = _finite_numeric_values(
            dataframe[column_name]
        )

        total_numeric_cells += len(
            values
        )

    if total_numeric_cells == 0:
        return 100.0

    outlier_count = sum(
        issue.affected_count
        for issue in issues
        if issue.code
        == "NUMERIC_IQR_OUTLIERS"
    )

    outlier_percentage = min(
        100.0,
        outlier_count
        / total_numeric_cells
        * 100,
    )

    return round(
        max(
            0.0,
            100.0 - outlier_percentage,
        ),
        2,
    )