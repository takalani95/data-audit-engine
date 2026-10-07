from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from src.ingestion.models import DatasetMetadata, IngestionResult
from src.ingestion.validators import validate_file


class DatasetLoadError(RuntimeError):
    """Raised when a validated dataset cannot be loaded."""


def _read_csv(file_bytes: bytes) -> pd.DataFrame:
    """Load CSV bytes into a DataFrame."""

    return pd.read_csv(BytesIO(file_bytes))


def _read_excel(file_bytes: bytes) -> pd.DataFrame:
    """Load Excel bytes into a DataFrame."""

    return pd.read_excel(BytesIO(file_bytes))


def load_dataset(
    file: BinaryIO,
    file_name: str,
) -> IngestionResult:
    """
    Validate and load a CSV or XLSX dataset.

    Returns a standardized IngestionResult containing
    the DataFrame, dataset metadata and warnings.
    """

    file_bytes = file.read()
    file_size_bytes = len(file_bytes)

    validate_file(
        file_name=file_name,
        file_size_bytes=file_size_bytes,
    )

    extension = Path(file_name).suffix.lower()

    try:
        if extension == ".csv":
            dataframe = _read_csv(file_bytes)

        elif extension == ".xlsx":
            dataframe = _read_excel(file_bytes)

        else:
            raise DatasetLoadError(
                f"No loader configured for '{extension}'."
            )

    except Exception as exc:
        raise DatasetLoadError(
            f"Unable to load '{file_name}': {exc}"
        ) from exc

    warnings: list[str] = []

    if dataframe.empty:
        warnings.append(
            "The dataset loaded successfully but contains no rows."
        )

    if dataframe.columns.duplicated().any():
        warnings.append(
            "Duplicate column names were detected."
        )

    metadata = DatasetMetadata(
        file_name=file_name,
        file_type=extension.removeprefix("."),
        file_size_bytes=file_size_bytes,
        rows=len(dataframe),
        columns=len(dataframe.columns),
        column_names=[
            str(column)
            for column in dataframe.columns
        ],
        memory_usage_bytes=int(
            dataframe.memory_usage(deep=True).sum()
        ),
    )

    return IngestionResult(
        dataframe=dataframe,
        metadata=metadata,
        warnings=warnings,
    )