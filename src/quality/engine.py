import pandas as pd

from src.profiling.models import DatasetProfile
from src.quality.checks import (
    check_constant_columns,
    check_duplicate_rows,
    check_high_missing_dataset,
    check_missing_values,
    check_unnamed_columns,
)
from src.quality.models import (
    QualityDimension,
    QualityIssue,
    QualityReport,
)


WEIGHTS = {
    "completeness": 25.0,
    "uniqueness": 15.0,
    "validity": 20.0,
    "consistency": 15.0,
    "structural_quality": 15.0,
    "statistical_health": 10.0,
}


def _score_completeness(
    profile: DatasetProfile,
) -> float:
    return max(
        0.0,
        100.0 - profile.missing_percentage,
    )


def _score_uniqueness(
    profile: DatasetProfile,
) -> float:
    return max(
        0.0,
        100.0 - profile.duplicate_percentage,
    )


def _score_structural_quality(
    profile: DatasetProfile,
) -> float:

    if profile.columns == 0:
        return 0.0

    unnamed_ratio = (
        len(profile.unnamed_columns)
        / profile.columns
    )

    constant_ratio = (
        len(profile.constant_columns)
        / profile.columns
    )

    penalty = (
        unnamed_ratio * 70.0
        + constant_ratio * 30.0
    )

    return max(
        0.0,
        100.0 - penalty,
    )


def _status_from_score_and_issues(
    score: float,
    critical_count: int,
    warning_count: int,
) -> str:
    """
    Determine operational quality status.

    The numerical score describes aggregate quality.

    Issue severity acts as a safety override so that
    serious localised problems cannot be hidden by a
    high aggregate score.
    """

    if score < 60:
        return "critical"

    if critical_count > 0:
        return "needs_attention"

    if score < 85:
        return "needs_attention"

    if warning_count > 0:
        return "needs_attention"

    return "good"


def run_quality_audit(
    dataframe: pd.DataFrame,
    profile: DatasetProfile,
) -> QualityReport:
    """
    Run deterministic quality checks.

    Only implemented dimensions contribute to the
    overall score. Unimplemented dimensions remain
    explicitly unassessed.
    """

    issues: list[QualityIssue] = []

    issues.extend(
        check_missing_values(
            dataframe,
            profile,
        )
    )

    issues.extend(
        check_duplicate_rows(
            dataframe,
            profile,
        )
    )

    issues.extend(
        check_unnamed_columns(
            dataframe,
            profile,
        )
    )

    issues.extend(
        check_constant_columns(
            dataframe,
            profile,
        )
    )

    issues.extend(
        check_high_missing_dataset(
            dataframe,
            profile,
        )
    )

    dimension_scores: dict[
        str,
        float | None,
    ] = {
        "completeness":
            _score_completeness(profile),

        "uniqueness":
            _score_uniqueness(profile),

        "validity":
            None,

        "consistency":
            None,

        "structural_quality":
            _score_structural_quality(profile),

        "statistical_health":
            None,
    }

    dimensions: dict[
        str,
        QualityDimension,
    ] = {}

    for name, weight in WEIGHTS.items():

        score = dimension_scores[name]

        dimension_issues = [
            issue
            for issue in issues
            if issue.category == name
        ]

        dimensions[name] = QualityDimension(
            name=name,
            score=(
                round(score, 2)
                if score is not None
                else None
            ),
            weight=weight,
            assessed=score is not None,
            issues=dimension_issues,
        )

    assessed_dimensions = [
        dimension
        for dimension in dimensions.values()
        if dimension.assessed
        and dimension.score is not None
    ]

    assessed_weight = sum(
        dimension.weight
        for dimension in assessed_dimensions
    )

    if assessed_weight == 0:
        overall_score = 0.0

    else:
        weighted_total = sum(
            dimension.score
            * dimension.weight
            for dimension in assessed_dimensions
            if dimension.score is not None
        )

        overall_score = (
            weighted_total
            / assessed_weight
        )

    overall_score = round(
        overall_score,
        2,
    )

    critical_count = sum(
        issue.severity == "critical"
        for issue in issues
    )

    warning_count = sum(
        issue.severity == "warning"
        for issue in issues
    )

    info_count = sum(
        issue.severity == "info"
        for issue in issues
    )

    status = _status_from_score_and_issues(
        score=overall_score,
        critical_count=critical_count,
        warning_count=warning_count,
    )

    return QualityReport(
        overall_score=overall_score,
        status=status,
        dimensions=dimensions,
        issues=issues,
        critical_count=critical_count,
        warning_count=warning_count,
        info_count=info_count,
    )