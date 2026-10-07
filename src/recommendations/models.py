from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Recommendation:
    """
    One deterministic recommendation generated from
    verified data-quality evidence.
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

    evidence: dict[str, Any] = field(
        default_factory=dict
    )