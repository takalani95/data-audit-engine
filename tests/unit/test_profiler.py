import pandas as pd

from src.profiling.profiler import (
    profile_dataset,
)


def test_profile_dataset_shape():
    dataframe = pd.DataFrame(
        {
            "customer_id": [1, 2, 3],
            "age": [25, 31, 42],
            "region": [
                "Gauteng",
                "Limpopo",
                "Gauteng",
            ],
        }
    )

    profile = profile_dataset(dataframe)

    assert profile.rows == 3
    assert profile.columns == 3
    assert profile.total_cells == 9


def test_detect_missing_values():
    dataframe = pd.DataFrame(
        {
            "age": [
                25,
                None,
                42,
                None,
            ]
        }
    )

    profile = profile_dataset(dataframe)

    age_profile = profile.column_profiles[0]

    assert age_profile.missing_count == 2
    assert age_profile.missing_percentage == 50.0


def test_detect_duplicate_rows():
    dataframe = pd.DataFrame(
        {
            "customer": [
                "A",
                "A",
                "B",
            ],
            "value": [
                100,
                100,
                200,
            ],
        }
    )

    profile = profile_dataset(dataframe)

    assert profile.duplicate_rows == 1


def test_detect_numeric_statistics():
    dataframe = pd.DataFrame(
        {
            "revenue": [
                100.0,
                200.0,
                300.0,
            ]
        }
    )

    profile = profile_dataset(dataframe)

    revenue = profile.column_profiles[0]

    assert revenue.semantic_type == "numeric"
    assert revenue.minimum == 100.0
    assert revenue.maximum == 300.0
    assert revenue.mean == 200.0
    assert revenue.median == 200.0


def test_detect_constant_column():
    dataframe = pd.DataFrame(
        {
            "country": [
                "South Africa",
                "South Africa",
                "South Africa",
            ]
        }
    )

    profile = profile_dataset(dataframe)

    assert "country" in profile.constant_columns


def test_detect_unnamed_columns():
    dataframe = pd.DataFrame(
        {
            "customer": ["A", "B"],
            "Unnamed: 3": [1, 2],
            "Unnamed: 4": [3, 4],
        }
    )

    profile = profile_dataset(dataframe)

    assert profile.unnamed_columns == [
        "Unnamed: 3",
        "Unnamed: 4",
    ]