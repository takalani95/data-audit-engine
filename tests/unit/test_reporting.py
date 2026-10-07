import pandas as pd

from src.ingestion.models import (
    DatasetMetadata,
)
from src.profiling.profiler import (
    profile_dataset,
)
from src.quality.engine import (
    run_quality_audit,
)
from src.recommendations.engine import (
    generate_recommendations,
)
from src.reporting.builder import (
    build_audit_report,
)
from src.reporting.models import (
    AuditReport,
    ReportDimension,
    ReportFinding,
    ReportRecommendation,
)


def test_audit_report_stores_dataset_summary():
    report = AuditReport(
        report_title=(
            "MASH LABS Data Quality Audit Report"
        ),
        file_name="customers.csv",
        file_type="csv",
        file_size_bytes=1024,
        rows=100,
        columns=5,
        missing_cells=10,
        missing_percentage=2.0,
        duplicate_rows=2,
        duplicate_percentage=2.0,
        quality_score=94.5,
        quality_status="needs_attention",
        critical_count=0,
        warning_count=2,
        info_count=1,
    )

    assert report.file_name == "customers.csv"
    assert report.rows == 100
    assert report.columns == 5
    assert report.quality_score == 94.5
    assert (
        report.quality_status
        == "needs_attention"
    )


def test_report_dimension_stores_score_and_weight():
    dimension = ReportDimension(
        name="Completeness",
        score=92.5,
        weight=25.0,
        assessed=True,
        issue_count=3,
    )

    assert dimension.name == "Completeness"
    assert dimension.score == 92.5
    assert dimension.weight == 25.0
    assert dimension.issue_count == 3


def test_report_finding_preserves_evidence():
    finding = ReportFinding(
        code="MISSING_VALUES",
        category="completeness",
        severity="critical",
        title="Missing values detected",
        description=(
            "Column 'ISP' contains missing values."
        ),
        column="ISP",
        affected_count=90,
        affected_percentage=90.0,
        evidence={
            "missing_count": 90,
        },
    )

    assert finding.column == "ISP"
    assert finding.affected_count == 90
    assert (
        finding.evidence["missing_count"]
        == 90
    )


def test_report_recommendation_stores_guidance():
    recommendation = ReportRecommendation(
        code="REC_MISSING_VALUES",
        priority="high",
        title="Investigate missing values",
        problem=(
            "The field contains substantial "
            "missing data."
        ),
        why_it_matters=(
            "Missing data may reduce coverage."
        ),
        recommended_action=(
            "Confirm whether the field is required."
        ),
        category="completeness",
        source_issue_code="MISSING_VALUES",
        column="ISP",
        affected_count=90,
        affected_percentage=90.0,
    )

    assert recommendation.priority == "high"
    assert recommendation.column == "ISP"
    assert (
        recommendation.source_issue_code
        == "MISSING_VALUES"
    )


def test_audit_report_defaults_to_empty_sections():
    report = AuditReport(
        report_title=(
            "MASH LABS Data Quality Audit Report"
        ),
        file_name="clean.csv",
        file_type="csv",
        file_size_bytes=100,
        rows=10,
        columns=2,
        missing_cells=0,
        missing_percentage=0.0,
        duplicate_rows=0,
        duplicate_percentage=0.0,
        quality_score=100.0,
        quality_status="good",
        critical_count=0,
        warning_count=0,
        info_count=0,
    )

    assert report.dimensions == []
    assert report.findings == []
    assert report.recommendations == []


def _build_metadata(
    dataframe: pd.DataFrame,
) -> DatasetMetadata:
    return DatasetMetadata(
        file_name="customers.csv",
        file_type="csv",
        file_size_bytes=2048,
        rows=len(dataframe),
        columns=len(dataframe.columns),
        column_names=[
            str(column)
            for column in dataframe.columns
        ],
        memory_usage_bytes=int(
            dataframe.memory_usage(
                deep=True
            ).sum()
        ),
    )


def test_builder_creates_complete_audit_report():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                None,
                "C",
                "D",
            ],
            "amount": [
                10,
                20,
                30,
                40,
            ],
        }
    )

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    assert report.report_title == (
        "MASH LABS Data Quality Audit Report"
    )

    assert report.file_name == "customers.csv"
    assert report.rows == 4
    assert report.columns == 2

    assert len(report.dimensions) == 6

    assert (
        report.quality_score
        == quality_report.overall_score
    )

    assert (
        report.quality_status
        == quality_report.status
    )


def test_builder_preserves_quality_findings():
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

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    report_codes = {
        finding.code
        for finding in report.findings
    }

    quality_codes = {
        issue.code
        for issue in quality_report.issues
    }

    assert report_codes == quality_codes


def test_builder_preserves_recommendations():
    dataframe = pd.DataFrame(
        {
            "customer": [
                None,
                None,
                None,
                "A",
            ]
        }
    )

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    assert len(
        report.recommendations
    ) == len(
        recommendations
    )

    source_codes = {
        recommendation.source_issue_code
        for recommendation
        in report.recommendations
    }

    assert "MISSING_VALUES" in source_codes


def test_builder_preserves_dimension_weights():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "B",
                "C",
                "D",
            ],
            "amount": [
                10,
                20,
                30,
                40,
            ],
        }
    )

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    total_weight = sum(
        dimension.weight
        for dimension in report.dimensions
    )

    assert total_weight == 100.0


def test_builder_sorts_findings_by_severity():
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

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    severity_rank = {
        "critical": 0,
        "warning": 1,
        "info": 2,
    }

    ranks = [
        severity_rank[finding.severity]
        for finding in report.findings
    ]

    assert ranks == sorted(ranks)


def test_builder_sorts_recommendations_by_priority():
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

    metadata = _build_metadata(
        dataframe
    )

    profile = profile_dataset(
        dataframe
    )

    quality_report = run_quality_audit(
        dataframe,
        profile,
    )

    recommendations = (
        generate_recommendations(
            quality_report
        )
    )

    report = build_audit_report(
        metadata=metadata,
        profile=profile,
        quality_report=quality_report,
        recommendations=recommendations,
    )

    priority_rank = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    ranks = [
        priority_rank[
            recommendation.priority
        ]
        for recommendation
        in report.recommendations
    ]

    assert ranks == sorted(ranks)