from io import BytesIO

import pandas as pd
import pytest

from src.ingestion.loader import load_dataset
from src.ingestion.validators import FileValidationError


def test_load_csv_successfully():
    csv_data = (
        b"customer_id,age,revenue\n"
        b"1,25,1000\n"
        b"2,31,1500\n"
        b"3,42,2100\n"
    )

    result = load_dataset(
        BytesIO(csv_data),
        "customers.csv",
    )

    assert isinstance(result.dataframe, pd.DataFrame)
    assert result.metadata.rows == 3
    assert result.metadata.columns == 3
    assert result.metadata.file_type == "csv"

    assert result.metadata.column_names == [
        "customer_id",
        "age",
        "revenue",
    ]


def test_reject_unsupported_file_type():
    fake_data = BytesIO(b"some fake content")

    with pytest.raises(FileValidationError):
        load_dataset(
            fake_data,
            "customers.txt",
        )


def test_reject_empty_file():
    with pytest.raises(FileValidationError):
        load_dataset(
            BytesIO(b""),
            "customers.csv",
        )


def test_metadata_matches_dataframe():
    csv_data = (
        b"name,region,sales\n"
        b"Store A,Gauteng,100\n"
        b"Store B,Limpopo,200\n"
    )

    result = load_dataset(
        BytesIO(csv_data),
        "sales.csv",
    )

    assert result.shape == (2, 3)
    assert result.metadata.rows == 2
    assert result.metadata.columns == 3
    assert result.metadata.file_size_bytes > 0
    assert result.metadata.memory_usage_bytes > 0