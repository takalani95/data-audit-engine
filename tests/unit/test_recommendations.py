import pandas as pd

from src.profiling.profiler import (
    profile_dataset,
)
from src.quality.engine import (
    run_quality_audit,
)
from src.quality.models import (
    QualityIssue,
)
from src.recommendations.engine import (
    generate_recommendations,
    recommendation_from_issue,
)
from src.recommendations.models import (
    Recommendation,
)


def test_recommendation_stores_actionable_guidance():
    recommendation = Recommendation(
        code="REC_MISSING_VALUES",
        priority="high",
        title="Investigate missing values",
        problem=(
            "A column contains substantial "
            "missing data."
        ),
        why_it_matters=(
            "Incomplete data may affect "
            "analysis or modelling."
        ),
        recommended_action=(
            "Confirm whether the field is "
            "required and investigate the "
            "upstream source if necessary."
        ),
        category="completeness",
        source_issue_code="MISSING_VALUES",
        column="customer",
        affected_count=25,
        affected_percentage=25.0,
        evidence={
            "missing_count": 25,
        },
    )

    assert recommendation.priority == "high"
    assert recommendation.column == "customer"
    assert recommendation.affected_count == 25
    assert (
        recommendation.source_issue_code
        == "MISSING_VALUES"
    )


def test_recommendation_can_exist_without_column():
    recommendation = Recommendation(
        code="REC_DUPLICATE_ROWS",
        priority="medium",
        title="Review duplicate records",
        problem=(
            "Duplicate rows were detected."
        ),
        why_it_matters=(
            "Duplicates may distort counts "
            "and aggregate calculations."
        ),
        recommended_action=(
            "Review duplicate records before "
            "removing them."
        ),
        category="uniqueness",
        source_issue_code="DUPLICATE_ROWS",
    )

    assert recommendation.column is None
    assert recommendation.affected_count == 0
    assert recommendation.evidence == {}


def test_missing_issue_generates_recommendation():
    issue = QualityIssue(
        code="MISSING_VALUES",
        category="completeness",
        severity="critical",
        title="Missing values detected",
        description=(
            "Column 'ISP' contains 90 missing values."
        ),
        column="ISP",
        affected_count=90,
        affected_percentage=90.0,
        evidence={
            "missing_count": 90,
        },
    )

    recommendation = recommendation_from_issue(
        issue
    )

    assert recommendation is not None
    assert recommendation.priority == "high"
    assert (
        recommendation.source_issue_code
        == "MISSING_VALUES"
    )
    assert recommendation.column == "ISP"
    assert recommendation.affected_count == 90


def test_warning_maps_to_medium_priority():
    issue = QualityIssue(
        code="SURROUNDING_WHITESPACE",
        category="consistency",
        severity="warning",
        title="Whitespace detected",
        description=(
            "Whitespace was detected."
        ),
        column="bank",
        affected_count=10,
        affected_percentage=10.0,
    )

    recommendation = recommendation_from_issue(
        issue
    )

    assert recommendation is not None
    assert recommendation.priority == "medium"


def test_info_maps_to_low_priority():
    issue = QualityIssue(
        code="EXTREME_SKEWNESS",
        category="statistical_health",
        severity="info",
        title="Skewness detected",
        description=(
            "A highly skewed distribution "
            "was detected."
        ),
        column="revenue",
    )

    recommendation = recommendation_from_issue(
        issue
    )

    assert recommendation is not None
    assert recommendation.priority == "low"


def test_unknown_issue_does_not_invent_recommendation():
    issue = QualityIssue(
        code="UNKNOWN_FUTURE_CHECK",
        category="future",
        severity="warning",
        title="Unknown issue",
        description=(
            "A future quality issue."
        ),
    )

    recommendation = recommendation_from_issue(
        issue
    )

    assert recommendation is None


def test_recommendation_preserves_issue_evidence():
    issue = QualityIssue(
        code="NUMERIC_IQR_OUTLIERS",
        category="statistical_health",
        severity="info",
        title="Numeric outliers detected",
        description=(
            "One numeric outlier was detected."
        ),
        column="revenue",
        affected_count=1,
        affected_percentage=10.0,
        evidence={
            "lower_bound": 0.0,
            "upper_bound": 100.0,
            "examples": [
                1000,
            ],
        },
    )

    recommendation = recommendation_from_issue(
        issue
    )

    assert recommendation is not None
    assert (
        recommendation.evidence["upper_bound"]
        == 100.0
    )
    assert (
        recommendation.evidence["examples"]
        == [1000]
    )


def test_quality_report_generates_recommendations():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                None,
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

    recommendations = generate_recommendations(
        report
    )

    assert len(recommendations) > 0

    source_codes = {
        recommendation.source_issue_code
        for recommendation in recommendations
    }

    assert "MISSING_VALUES" in source_codes


def test_recommendations_are_sorted_by_priority():
    dataframe = pd.DataFrame(
        {
            "customer": [
                None,
                None,
                None,
                " A ",
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

    recommendations = generate_recommendations(
        report
    )

    priorities = [
        recommendation.priority
        for recommendation in recommendations
    ]

    priority_rank = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    ranks = [
        priority_rank[priority]
        for priority in priorities
    ]

    assert ranks == sorted(ranks)