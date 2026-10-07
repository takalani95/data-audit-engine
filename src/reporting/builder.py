from __future__ import annotations

from src.ingestion.models import (
    DatasetMetadata,
)
from src.profiling.models import (
    DatasetProfile,
)
from src.quality.models import (
    QualityReport,
)
from src.recommendations.models import (
    Recommendation,
)
from src.reporting.models import (
    AuditReport,
    ReportDimension,
    ReportFinding,
    ReportRecommendation,
)


REPORT_TITLE = (
    "MASH LABS Data Quality Audit Report"
)


DIMENSION_DISPLAY_NAMES = {
    "completeness": "Completeness",
    "uniqueness": "Uniqueness",
    "validity": "Validity",
    "consistency": "Consistency",
    "structural_quality": "Structural Quality",
    "statistical_health": "Statistical Health",
}


def _build_dimensions(
    quality_report: QualityReport,
) -> list[ReportDimension]:
    """
    Convert quality dimensions into stable,
    report-ready objects.
    """

    dimensions: list[
        ReportDimension
    ] = []

    for name, dimension in (
        quality_report.dimensions.items()
    ):

        dimensions.append(
            ReportDimension(
                name=(
                    DIMENSION_DISPLAY_NAMES.get(
                        name,
                        name.replace(
                            "_",
                            " ",
                        ).title(),
                    )
                ),
                score=dimension.score,
                weight=dimension.weight,
                assessed=dimension.assessed,
                issue_count=len(
                    dimension.issues
                ),
            )
        )

    return dimensions


def _build_findings(
    quality_report: QualityReport,
) -> list[ReportFinding]:
    """
    Convert verified QualityIssue objects into
    report-ready findings.

    No new findings are inferred here.
    """

    severity_order = {
        "critical": 0,
        "warning": 1,
        "info": 2,
    }

    sorted_issues = sorted(
        quality_report.issues,
        key=lambda issue: (
            severity_order.get(
                issue.severity,
                99,
            ),
            issue.category,
            issue.column or "",
            issue.code,
        ),
    )

    findings: list[
        ReportFinding
    ] = []

    for issue in sorted_issues:

        findings.append(
            ReportFinding(
                code=issue.code,
                category=issue.category,
                severity=issue.severity,
                title=issue.title,
                description=issue.description,
                column=issue.column,
                affected_count=(
                    issue.affected_count
                ),
                affected_percentage=(
                    issue.affected_percentage
                ),
                evidence=dict(
                    issue.evidence
                ),
            )
        )

    return findings


def _build_recommendations(
    recommendations: list[Recommendation],
) -> list[ReportRecommendation]:
    """
    Convert deterministic recommendations into
    report-ready objects.
    """

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    sorted_recommendations = sorted(
        recommendations,
        key=lambda recommendation: (
            priority_order.get(
                recommendation.priority,
                99,
            ),
            recommendation.category,
            recommendation.column or "",
            recommendation.code,
        ),
    )

    report_recommendations: list[
        ReportRecommendation
    ] = []

    for recommendation in (
        sorted_recommendations
    ):

        report_recommendations.append(
            ReportRecommendation(
                code=recommendation.code,
                priority=(
                    recommendation.priority
                ),
                title=recommendation.title,
                problem=recommendation.problem,
                why_it_matters=(
                    recommendation.why_it_matters
                ),
                recommended_action=(
                    recommendation.recommended_action
                ),
                category=(
                    recommendation.category
                ),
                source_issue_code=(
                    recommendation.source_issue_code
                ),
                column=recommendation.column,
                affected_count=(
                    recommendation.affected_count
                ),
                affected_percentage=(
                    recommendation.affected_percentage
                ),
            )
        )

    return report_recommendations


def build_audit_report(
    metadata: DatasetMetadata,
    profile: DatasetProfile,
    quality_report: QualityReport,
    recommendations: list[Recommendation],
) -> AuditReport:
    """
    Build the complete deterministic MASH LABS
    Data Quality Audit Report model.

    This function does not perform profiling,
    quality assessment, recommendation generation,
    or rendering.

    It only assembles already verified results into
    one stable reporting object.
    """

    return AuditReport(
        report_title=REPORT_TITLE,

        file_name=metadata.file_name,
        file_type=metadata.file_type,
        file_size_bytes=(
            metadata.file_size_bytes
        ),

        rows=profile.rows,
        columns=profile.columns,

        missing_cells=(
            profile.missing_cells
        ),
        missing_percentage=(
            profile.missing_percentage
        ),

        duplicate_rows=(
            profile.duplicate_rows
        ),
        duplicate_percentage=(
            profile.duplicate_percentage
        ),

        quality_score=(
            quality_report.overall_score
        ),
        quality_status=(
            quality_report.status
        ),

        critical_count=(
            quality_report.critical_count
        ),
        warning_count=(
            quality_report.warning_count
        ),
        info_count=(
            quality_report.info_count
        ),

        dimensions=_build_dimensions(
            quality_report
        ),

        findings=_build_findings(
            quality_report
        ),

        recommendations=(
            _build_recommendations(
                recommendations
            )
        ),
    )