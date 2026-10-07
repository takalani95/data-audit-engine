from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from src.quality.models import QualityIssue


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


def _severity_from_percentage(
    percentage: float,
) -> str:
    """
    Convert an affected percentage into an issue severity.
    """

    if percentage >= 20:
        return "critical"

    if percentage >= 5:
        return "warning"

    return "info"


def _is_text_value(
    value: Any,
) -> bool:
    """
    Return True when the value is a string.
    """

    return isinstance(value, str)


def _normalise_text(
    value: str,
) -> str:
    """
    Create a conservative comparison representation.

    This normalisation is used only for comparison.
    Original dataset values are never modified.
    """

    return " ".join(
        value.strip().casefold().split()
    )


def check_surrounding_whitespace(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect text values containing leading or trailing
    whitespace.
    """

    issues: list[QualityIssue] = []

    for column_name in dataframe.columns:

        series = dataframe[column_name]

        text_values = series[
            series.map(_is_text_value)
        ]

        if text_values.empty:
            continue

        whitespace_mask = text_values.map(
            lambda value: value != value.strip()
        )

        affected_count = int(
            whitespace_mask.sum()
        )

        if affected_count == 0:
            continue

        affected_percentage = _percentage(
            affected_count,
            len(text_values),
        )

        examples = (
            text_values[
                whitespace_mask
            ]
            .astype(str)
            .drop_duplicates()
            .head(5)
            .tolist()
        )

        issues.append(
            QualityIssue(
                code="SURROUNDING_WHITESPACE",
                category="consistency",
                severity=_severity_from_percentage(
                    affected_percentage
                ),
                title="Surrounding whitespace detected",
                description=(
                    f"Column '{column_name}' contains "
                    f"{affected_count:,} text value(s) "
                    "with leading or trailing whitespace "
                    f"({affected_percentage:.2f}% of "
                    "text values)."
                ),
                column=str(column_name),
                affected_count=affected_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "examples": examples,
                    "text_value_count":
                        int(len(text_values)),
                },
            )
        )

    return issues


def check_normalised_text_variants(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Detect multiple textual representations that collapse
    to the same conservative normalised value.

    Examples:
        FNB
        fnb
        Fnb

    or:
        Johannesburg
        johannesburg

    Whitespace-only differences are excluded from the
    affected count here because they are already handled
    by SURROUNDING_WHITESPACE.
    """

    issues: list[QualityIssue] = []

    for column_name in dataframe.columns:

        series = dataframe[column_name]

        text_values = series[
            series.map(_is_text_value)
        ]

        if text_values.empty:
            continue

        clean_text_values = text_values[
            text_values.map(
                lambda value: value.strip() != ""
            )
        ]

        if clean_text_values.empty:
            continue

        groups: dict[
            str,
            dict[str, int],
        ] = defaultdict(dict)

        for value in clean_text_values:

            stripped_value = value.strip()

            normalised_value = _normalise_text(
                stripped_value
            )

            current_count = groups[
                normalised_value
            ].get(
                stripped_value,
                0,
            )

            groups[
                normalised_value
            ][
                stripped_value
            ] = current_count + 1

        inconsistent_groups = []

        affected_count = 0

        for normalised_value, variants in groups.items():

            if len(variants) <= 1:
                continue

            variant_counts = sorted(
                variants.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )

            dominant_variant = (
                variant_counts[0][0]
            )

            dominant_count = (
                variant_counts[0][1]
            )

            total_group_count = sum(
                variants.values()
            )

            minority_count = (
                total_group_count
                - dominant_count
            )

            if minority_count <= 0:
                continue

            affected_count += minority_count

            inconsistent_groups.append(
                {
                    "normalised_value":
                        normalised_value,
                    "dominant_variant":
                        dominant_variant,
                    "variants":
                        variants,
                    "affected_count":
                        minority_count,
                }
            )

        if affected_count == 0:
            continue

        affected_percentage = _percentage(
            affected_count,
            len(clean_text_values),
        )

        issues.append(
            QualityIssue(
                code="TEXT_REPRESENTATION_VARIANTS",
                category="consistency",
                severity=_severity_from_percentage(
                    affected_percentage
                ),
                title=(
                    "Inconsistent text representations "
                    "detected"
                ),
                description=(
                    f"Column '{column_name}' contains "
                    f"{affected_count:,} value(s) using "
                    "non-dominant casing or textual "
                    "representation "
                    f"({affected_percentage:.2f}% of "
                    "non-blank text values)."
                ),
                column=str(column_name),
                affected_count=affected_count,
                affected_percentage=(
                    affected_percentage
                ),
                evidence={
                    "groups":
                        inconsistent_groups[:10],
                    "group_count":
                        len(inconsistent_groups),
                },
            )
        )

    return issues


def run_consistency_checks(
    dataframe: pd.DataFrame,
) -> list[QualityIssue]:
    """
    Run all currently implemented consistency checks.
    """

    issues: list[QualityIssue] = []

    issues.extend(
        check_surrounding_whitespace(
            dataframe
        )
    )

    issues.extend(
        check_normalised_text_variants(
            dataframe
        )
    )

    return issues


def calculate_consistency_score(
    dataframe: pd.DataFrame,
    issues: list[QualityIssue],
) -> float:
    """
    Calculate an explainable consistency score.

    The score is based on the proportion of dataset cells
    affected by deterministic consistency findings.

    A cell can theoretically appear in more than one
    consistency finding, so the final deduction is capped
    at 100%.
    """

    total_cells = int(
        dataframe.shape[0]
        * dataframe.shape[1]
    )

    if total_cells == 0:
        return 100.0

    score_codes = {
        "SURROUNDING_WHITESPACE",
        "TEXT_REPRESENTATION_VARIANTS",
    }

    affected_count = sum(
        issue.affected_count
        for issue in issues
        if issue.code in score_codes
    )

    affected_percentage = min(
        100.0,
        affected_count
        / total_cells
        * 100,
    )

    return round(
        max(
            0.0,
            100.0 - affected_percentage,
        ),
        2,
    )