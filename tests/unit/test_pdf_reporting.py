from src.reporting.models import (
    AuditReport,
    ReportDimension,
    ReportFinding,
    ReportRecommendation,
)
from src.reporting.pdf_renderer import (
    render_audit_report_pdf,
)


def _sample_report() -> AuditReport:
    return AuditReport(
        report_title=(
            "MASH LABS Data Quality Audit Report"
        ),
        file_name="customers.csv",
        file_type="csv",
        file_size_bytes=2048,
        rows=100,
        columns=5,
        missing_cells=25,
        missing_percentage=5.0,
        duplicate_rows=2,
        duplicate_percentage=2.0,
        quality_score=92.5,
        quality_status="needs_attention",
        critical_count=1,
        warning_count=1,
        info_count=0,
        dimensions=[
            ReportDimension(
                name="Completeness",
                score=90.0,
                weight=25.0,
                assessed=True,
                issue_count=1,
            ),
            ReportDimension(
                name="Uniqueness",
                score=98.0,
                weight=15.0,
                assessed=True,
                issue_count=1,
            ),
            ReportDimension(
                name="Validity",
                score=100.0,
                weight=20.0,
                assessed=True,
                issue_count=0,
            ),
            ReportDimension(
                name="Consistency",
                score=100.0,
                weight=15.0,
                assessed=True,
                issue_count=0,
            ),
            ReportDimension(
                name="Structural Quality",
                score=100.0,
                weight=15.0,
                assessed=True,
                issue_count=0,
            ),
            ReportDimension(
                name="Statistical Health",
                score=100.0,
                weight=10.0,
                assessed=True,
                issue_count=0,
            ),
        ],
        findings=[
            ReportFinding(
                code="MISSING_VALUES",
                category="completeness",
                severity="critical",
                title="Missing values detected",
                description=(
                    "Column 'email' contains "
                    "missing values."
                ),
                column="email",
                affected_count=25,
                affected_percentage=25.0,
                evidence={
                    "missing_count": 25,
                },
            ),
        ],
        recommendations=[
            ReportRecommendation(
                code="REC_MISSING_VALUES",
                priority="high",
                title="Investigate missing values",
                problem=(
                    "Column 'email' contains "
                    "missing values."
                ),
                why_it_matters=(
                    "Missing data may reduce coverage."
                ),
                recommended_action=(
                    "Confirm whether the field is "
                    "required and investigate the "
                    "upstream source."
                ),
                category="completeness",
                source_issue_code=(
                    "MISSING_VALUES"
                ),
                column="email",
                affected_count=25,
                affected_percentage=25.0,
            ),
        ],
    )


def test_pdf_renderer_returns_bytes():
    pdf = render_audit_report_pdf(
        _sample_report()
    )

    assert isinstance(
        pdf,
        bytes,
    )


def test_pdf_renderer_creates_pdf_signature():
    pdf = render_audit_report_pdf(
        _sample_report()
    )

    assert pdf.startswith(
        b"%PDF"
    )


def test_pdf_renderer_creates_nontrivial_document():
    pdf = render_audit_report_pdf(
        _sample_report()
    )

    assert len(pdf) > 1000


def test_pdf_renderer_handles_empty_sections():
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
        dimensions=[],
        findings=[],
        recommendations=[],
    )

    pdf = render_audit_report_pdf(
        report
    )

    assert pdf.startswith(
        b"%PDF"
    )

    assert len(pdf) > 1000