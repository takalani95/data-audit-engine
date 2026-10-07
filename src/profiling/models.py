from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnProfile:
    """Profile information for one dataset column."""

    name: str
    pandas_dtype: str
    semantic_type: str

    total_rows: int
    non_null_count: int
    missing_count: int
    missing_percentage: float

    unique_count: int
    unique_percentage: float

    is_possible_identifier: bool = False
    is_constant: bool = False

    minimum: Any = None
    maximum: Any = None
    mean: float | None = None
    median: float | None = None
    standard_deviation: float | None = None

    sample_values: list[Any] = field(default_factory=list)


@dataclass
class DatasetProfile:
    """Complete structural profile of a dataset."""

    rows: int
    columns: int

    total_cells: int
    missing_cells: int
    missing_percentage: float

    duplicate_rows: int
    duplicate_percentage: float

    column_profiles: list[ColumnProfile]

    type_counts: dict[str, int]

    constant_columns: list[str]
    possible_identifier_columns: list[str]
    unnamed_columns: list[str]