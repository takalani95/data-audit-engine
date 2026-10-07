from dataclasses import dataclass, field
from typing import Any


@dataclass
class QualityIssue:
    """One explainable data-quality finding."""

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
class QualityDimension:
    """Score and findings for one quality dimension."""

    name: str
    score: float | None
    weight: float
    assessed: bool

    issues: list[QualityIssue] = field(
        default_factory=list
    )


@dataclass
class QualityReport:
    """Complete deterministic data-quality assessment."""

    overall_score: float
    status: str

    dimensions: dict[str, QualityDimension]
    issues: list[QualityIssue]

    critical_count: int
    warning_count: int
    info_count: int