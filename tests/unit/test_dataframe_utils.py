import pandas as pd

from src.visualization.dataframe_utils import (
    make_dataframe_display_safe,
)


def test_mixed_object_column_becomes_string():
    dataframe = pd.DataFrame(
        {
            "Time To Attend": [
                51,
                "1 hour 51 minutes",
                None,
            ]
        }
    )

    safe_dataframe = (
        make_dataframe_display_safe(
            dataframe
        )
    )

    assert (
        str(
            safe_dataframe[
                "Time To Attend"
            ].dtype
        )
        == "string"
    )


def test_original_dataframe_is_not_modified():
    dataframe = pd.DataFrame(
        {
            "mixed": [
                1,
                "text",
            ]
        }
    )

    original_dtype = dataframe[
        "mixed"
    ].dtype

    make_dataframe_display_safe(
        dataframe
    )

    assert (
        dataframe["mixed"].dtype
        == original_dtype
    )


def test_numeric_column_remains_numeric():
    dataframe = pd.DataFrame(
        {
            "amount": [
                10,
                20,
                30,
            ]
        }
    )

    safe_dataframe = (
        make_dataframe_display_safe(
            dataframe
        )
    )

    assert pd.api.types.is_numeric_dtype(
        safe_dataframe["amount"]
    )