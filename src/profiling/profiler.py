from typing import Any

import pandas as pd

from src.profiling.models import (
    ColumnProfile,
    DatasetProfile,
)
from src.profiling.type_detector import (
    detect_semantic_type,
    is_possible_identifier,
)


def _safe_sample_values(
    series: pd.Series,
    limit: int = 5,
) -> list[Any]:
    """Return a small set of non-null example values."""

    values = (
        series
        .dropna()
        .drop_duplicates()
        .head(limit)
        .tolist()
    )

    return values


def _profile_column(
    series: pd.Series,
    column_name: str,
) -> ColumnProfile:
    """Generate a profile for one column."""

    total_rows = len(series)

    non_null_count = int(
        series.notna().sum()
    )

    missing_count = int(
        series.isna().sum()
    )

    if total_rows:
        missing_percentage = (
            missing_count / total_rows
        ) * 100
    else:
        missing_percentage = 0.0

    unique_count = int(
        series.nunique(dropna=True)
    )

    if non_null_count:
        unique_percentage = (
            unique_count / non_null_count
        ) * 100
    else:
        unique_percentage = 0.0

    possible_identifier = (
        is_possible_identifier(
            series,
            column_name,
        )
    )

    semantic_type = detect_semantic_type(
        series,
        column_name,
    )

    is_constant = (
        unique_count <= 1
        and non_null_count > 0
    )

    minimum = None
    maximum = None
    mean = None
    median = None
    standard_deviation = None

    if semantic_type == "numeric":

        numeric_series = pd.to_numeric(
            series,
            errors="coerce",
        )

        if numeric_series.notna().any():

            minimum = numeric_series.min()
            maximum = numeric_series.max()

            mean = float(
                numeric_series.mean()
            )

            median = float(
                numeric_series.median()
            )

            std_value = numeric_series.std()

            if pd.notna(std_value):
                standard_deviation = float(
                    std_value
                )

    return ColumnProfile(
        name=str(column_name),
        pandas_dtype=str(series.dtype),
        semantic_type=semantic_type,

        total_rows=total_rows,
        non_null_count=non_null_count,

        missing_count=missing_count,
        missing_percentage=round(
            missing_percentage,
            2,
        ),

        unique_count=unique_count,
        unique_percentage=round(
            unique_percentage,
            2,
        ),

        is_possible_identifier=possible_identifier,
        is_constant=is_constant,

        minimum=minimum,
        maximum=maximum,
        mean=mean,
        median=median,
        standard_deviation=standard_deviation,

        sample_values=_safe_sample_values(
            series
        ),
    )


def profile_dataset(
    dataframe: pd.DataFrame,
) -> DatasetProfile:
    """Generate a complete structural dataset profile."""

    rows, columns = dataframe.shape

    total_cells = rows * columns

    missing_cells = int(
        dataframe.isna().sum().sum()
    )

    if total_cells:
        missing_percentage = (
            missing_cells / total_cells
        ) * 100
    else:
        missing_percentage = 0.0

    duplicate_rows = int(
        dataframe.duplicated().sum()
    )

    if rows:
        duplicate_percentage = (
            duplicate_rows / rows
        ) * 100
    else:
        duplicate_percentage = 0.0

    column_profiles = [
        _profile_column(
            dataframe[column],
            str(column),
        )
        for column in dataframe.columns
    ]

    type_counts: dict[str, int] = {}

    for profile in column_profiles:
        type_counts[profile.semantic_type] = (
            type_counts.get(
                profile.semantic_type,
                0,
            )
            + 1
        )

    constant_columns = [
        profile.name
        for profile in column_profiles
        if profile.is_constant
    ]

    possible_identifier_columns = [
        profile.name
        for profile in column_profiles
        if profile.is_possible_identifier
    ]

    unnamed_columns = [
        str(column)
        for column in dataframe.columns
        if str(column)
        .lower()
        .startswith("unnamed:")
    ]

    return DatasetProfile(
        rows=rows,
        columns=columns,

        total_cells=total_cells,

        missing_cells=missing_cells,
        missing_percentage=round(
            missing_percentage,
            2,
        ),

        duplicate_rows=duplicate_rows,
        duplicate_percentage=round(
            duplicate_percentage,
            2,
        ),

        column_profiles=column_profiles,

        type_counts=type_counts,

        constant_columns=constant_columns,

        possible_identifier_columns=(
            possible_identifier_columns
        ),

        unnamed_columns=unnamed_columns,
    )