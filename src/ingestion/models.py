from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class DatasetMetadata:
    """Basic metadata describing an ingested dataset."""

    file_name: str
    file_type: str
    file_size_bytes: int
    rows: int
    columns: int
    column_names: list[str]
    memory_usage_bytes: int


@dataclass
class IngestionResult:
    """Standard result returned by the ingestion engine."""

    dataframe: pd.DataFrame
    metadata: DatasetMetadata
    warnings: list[str]

    @property
    def shape(self) -> tuple[int, int]:
        return self.dataframe.shape

    def summary(self) -> dict[str, Any]:
        return {
            "file_name": self.metadata.file_name,
            "file_type": self.metadata.file_type,
            "file_size_bytes": self.metadata.file_size_bytes,
            "rows": self.metadata.rows,
            "columns": self.metadata.columns,
            "memory_usage_bytes": self.metadata.memory_usage_bytes,
            "warnings": self.warnings,
        }