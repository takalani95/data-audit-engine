from __future__ import annotations

from dataclasses import dataclass

from src.quality.models import (
    QualityIssue,
    QualityReport,
)
from src.recommendations.models import (
    Recommendation,
)


@dataclass(frozen=True)
class RecommendationRule:
    """
    Controlled recommendation guidance for one
    known data-quality issue type.
    """

    recommendation_code: str
    title: str
    why_it_matters: str
    recommended_action: str


RECOMMENDATION_RULES: dict[
    str,
    RecommendationRule,
] = {
    "MISSING_VALUES": RecommendationRule(
        recommendation_code="REC_MISSING_VALUES",
        title="Investigate missing values",
        why_it_matters=(
            "Missing data can reduce coverage and may "
            "distort reporting, analysis, or modelling "
            "when the field is expected to be populated."
        ),
        recommended_action=(
            "Confirm whether the field is required. "
            "If required, investigate the upstream "
            "collection or source process. If optional, "
            "document the business rule before deciding "
            "whether to exclude, retain, or impute "
            "missing values."
        ),
    ),

    "DUPLICATE_ROWS": RecommendationRule(
        recommendation_code="REC_DUPLICATE_ROWS",
        title="Review duplicate records",
        why_it_matters=(
            "Duplicate records can inflate counts, "
            "totals, frequencies, and model training "
            "observations."
        ),
        recommended_action=(
            "Review the duplicate records against the "
            "business process and expected record grain. "
            "Remove or consolidate records only after "
            "confirming that they are true duplicates."
        ),
    ),

    "UNNAMED_COLUMN": RecommendationRule(
        recommendation_code="REC_UNNAMED_COLUMN",
        title="Review unnamed columns",
        why_it_matters=(
            "Unnamed columns often indicate exported "
            "indexes, formatting artefacts, or an "
            "incorrect header structure."
        ),
        recommended_action=(
            "Inspect the source file and confirm whether "
            "the column contains meaningful business "
            "data. Rename legitimate fields and remove "
            "export artefacts only after verification."
        ),
    ),

    "CONSTANT_COLUMN": RecommendationRule(
        recommendation_code="REC_CONSTANT_COLUMN",
        title="Review constant columns",
        why_it_matters=(
            "A column containing only one value usually "
            "provides little analytical variation and "
            "may indicate redundant or incorrectly "
            "loaded data."
        ),
        recommended_action=(
            "Confirm whether the constant value is "
            "expected. Retain the field if it has "
            "business or audit meaning; otherwise "
            "consider excluding it from analytical "
            "features."
        ),
    ),

    "BLANK_STRING": RecommendationRule(
        recommendation_code="REC_BLANK_STRING",
        title="Standardise blank text values",
        why_it_matters=(
            "Blank or whitespace-only text can behave "
            "differently from true missing values and "
            "can create inconsistent filtering, "
            "grouping, and validation results."
        ),
        recommended_action=(
            "Confirm whether blank text represents "
            "missing information. If so, standardise it "
            "to the dataset's approved missing-value "
            "representation before downstream use."
        ),
    ),

    "INFINITE_VALUE": RecommendationRule(
        recommendation_code="REC_INFINITE_VALUE",
        title="Investigate infinite numeric values",
        why_it_matters=(
            "Infinite values can break statistical "
            "calculations, visualisations, feature "
            "engineering, and machine-learning models."
        ),
        recommended_action=(
            "Trace the affected values to their source "
            "or calculation. Correct invalid arithmetic "
            "or transformation logic before replacing "
            "the values."
        ),
    ),

    "MIXED_PYTHON_TYPES": RecommendationRule(
        recommendation_code="REC_MIXED_TYPES",
        title="Review mixed value types",
        why_it_matters=(
            "Mixed underlying value types can make "
            "sorting, comparison, conversion, and "
            "modelling behaviour unpredictable."
        ),
        recommended_action=(
            "Review the affected column and determine "
            "its intended semantic type. Standardise "
            "values only after confirming the correct "
            "business representation."
        ),
    ),

    "SURROUNDING_WHITESPACE": RecommendationRule(
        recommendation_code="REC_WHITESPACE",
        title="Standardise surrounding whitespace",
        why_it_matters=(
            "Leading or trailing whitespace can cause "
            "visually identical values to be treated as "
            "different categories or keys."
        ),
        recommended_action=(
            "Review the affected values and, where "
            "appropriate, trim leading and trailing "
            "whitespace during data preparation or at "
            "the upstream source."
        ),
    ),

    "TEXT_REPRESENTATION_VARIANTS": RecommendationRule(
        recommendation_code="REC_TEXT_VARIANTS",
        title="Standardise text representations",
        why_it_matters=(
            "Different casing or textual representations "
            "of the same normalised value can fragment "
            "categories and distort grouping or counts."
        ),
        recommended_action=(
            "Define the approved representation for the "
            "affected values and standardise them using "
            "an explicit transformation or reference "
            "mapping."
        ),
    ),

    "NUMERIC_IQR_OUTLIERS": RecommendationRule(
        recommendation_code="REC_NUMERIC_OUTLIERS",
        title="Review numeric outliers",
        why_it_matters=(
            "Extreme numeric observations can materially "
            "influence averages, statistical summaries, "
            "visualisations, and some machine-learning "
            "models."
        ),
        recommended_action=(
            "Investigate the flagged observations in "
            "business context. Confirm whether they are "
            "valid extreme events, data-entry errors, "
            "or transformation problems before deciding "
            "whether any treatment is appropriate."
        ),
    ),

    "EXTREME_SKEWNESS": RecommendationRule(
        recommendation_code="REC_EXTREME_SKEWNESS",
        title="Review highly skewed distribution",
        why_it_matters=(
            "Strong skewness may affect statistical "
            "summaries and modelling assumptions, "
            "although it can also be a legitimate "
            "property of the data."
        ),
        recommended_action=(
            "Inspect the distribution and its business "
            "meaning before applying any transformation. "
            "For modelling, consider whether robust "
            "methods or a justified transformation are "
            "appropriate."
        ),
    ),
}


def _priority_from_severity(
    severity: str,
) -> str:
    """
    Convert issue severity into recommendation priority.
    """

    mapping = {
        "critical": "high",
        "warning": "medium",
        "info": "low",
    }

    return mapping.get(
        severity,
        "low",
    )


def _build_problem(
    issue: QualityIssue,
) -> str:
    """
    Preserve the verified issue description as the
    recommendation's problem statement.
    """

    return issue.description


def recommendation_from_issue(
    issue: QualityIssue,
) -> Recommendation | None:
    """
    Convert one recognised QualityIssue into a
    deterministic Recommendation.

    Unknown issue codes are deliberately ignored rather
    than receiving invented generic advice.
    """

    rule = RECOMMENDATION_RULES.get(
        issue.code
    )

    if rule is None:
        return None

    return Recommendation(
        code=rule.recommendation_code,
        priority=_priority_from_severity(
            issue.severity
        ),
        title=rule.title,
        problem=_build_problem(issue),
        why_it_matters=rule.why_it_matters,
        recommended_action=(
            rule.recommended_action
        ),
        category=issue.category,
        source_issue_code=issue.code,
        column=issue.column,
        affected_count=issue.affected_count,
        affected_percentage=(
            issue.affected_percentage
        ),
        evidence=dict(issue.evidence),
    )


def generate_recommendations(
    report: QualityReport,
) -> list[Recommendation]:
    """
    Generate recommendations from verified quality
    findings.

    The quality engine remains the source of truth.
    This function does not discover new issues.
    """

    recommendations: list[
        Recommendation
    ] = []

    for issue in report.issues:

        recommendation = (
            recommendation_from_issue(
                issue
            )
        )

        if recommendation is not None:
            recommendations.append(
                recommendation
            )

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    recommendations.sort(
        key=lambda recommendation: (
            priority_order.get(
                recommendation.priority,
                99,
            ),
            recommendation.category,
            recommendation.column or "",
            recommendation.code,
        )
    )

    return recommendations