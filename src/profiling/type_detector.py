import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
)


def is_possible_identifier(
    series: pd.Series,
    column_name: str,
) -> bool:
    """
    Determine whether a column appears to represent
    a record identifier.
    """

    non_null = series.dropna()

    if len(non_null) == 0:
        return False

    unique_ratio = non_null.nunique() / len(non_null)

    name = column_name.lower().strip()

    identifier_terms = (
        "id",
        "identifier",
        "number",
        "no",
        "code",
        "key",
        "uuid",
        "guid",
    )

    name_suggests_identifier = any(
        term == name
        or name.endswith(f"_{term}")
        or name.startswith(f"{term}_")
        for term in identifier_terms
    )

    return (
        unique_ratio >= 0.98
        and name_suggests_identifier
    )


def detect_semantic_type(
    series: pd.Series,
    column_name: str,
) -> str:
    """
    Infer a high-level semantic type for a column.
    """

    if is_possible_identifier(
        series,
        column_name,
    ):
        return "identifier"

    if is_bool_dtype(series):
        return "boolean"

    if is_datetime64_any_dtype(series):
        return "datetime"

    if is_numeric_dtype(series):
        return "numeric"

    non_null = series.dropna()

    if len(non_null) == 0:
        return "unknown"

    unique_count = non_null.nunique()

    unique_ratio = (
        unique_count / len(non_null)
    )

    if (
        unique_count <= 50
        or unique_ratio <= 0.20
    ):
        return "categorical"

    return "text"