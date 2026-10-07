from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportDimension:
    """
    Report-ready representation of one data-quality
    dimension.
    """

    name: str
    score: float | None
    weight: float
    assessed: bool
    issue_count: int


@dataclass
class ReportFinding:
    """
    Report-ready representation of one verified
    quality finding.
    """

    code: str
    category: str
    severity: str
    title: str
    description: str

    column: str | None = None

    affected_count: int = 0
    affected_percentage: float = 0.0

    evidence: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ReportRecommendation:
    """
    Report-ready representation of one deterministic
    recommendation.
    """

    code: str
    priority: str
    title: str

    problem: str
    why_it_matters: str
    recommended_action: str

    category: str
    source_issue_code: str

    column: str | None = None

    affected_count: int = 0
    affected_percentage: float = 0.0


@dataclass
class AuditReport:
    """
    Complete deterministic representation of a
    MASH LABS Data Quality Audit Report.

    This model contains report content only. Rendering
    to PDF, HTML, or another output format belongs to
    a separate layer.
    """

    report_title: str

    file_name: str
    file_type: str
    file_size_bytes: int

    rows: int
    columns: int

    missing_cells: int
    missing_percentage: float

    duplicate_rows: int
    duplicate_percentage: float

    quality_score: float
    quality_status: str

    critical_count: int
    warning_count: int
    info_count: int

    dimensions: list[ReportDimension] = field(
        default_factory=list
    )

    findings: list[ReportFinding] = field(
        default_factory=list
    )

    recommendations: list[
        ReportRecommendation
    ] = field(
        default_factory=list
    )