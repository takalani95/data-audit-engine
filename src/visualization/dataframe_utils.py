from __future__ import annotations

import pandas as pd


def make_dataframe_display_safe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return a copy of a DataFrame that is safe for
    Streamlit / PyArrow rendering.

    The original dataframe is never modified.

    Object columns containing mixed Python types are
    converted to nullable strings for display only.
    Numeric, datetime and boolean columns retain their
    original types whenever possible.
    """

    safe_dataframe = dataframe.copy()

    for column_name in safe_dataframe.columns:

        series = safe_dataframe[column_name]

        if series.dtype != "object":
            continue

        non_null = series.dropna()

        if non_null.empty:
            safe_dataframe[column_name] = (
                series.astype("string")
            )
            continue

        python_types = {
            type(value)
            for value in non_null
        }

        if len(python_types) > 1:
            safe_dataframe[column_name] = (
                series.astype("string")
            )

    return safe_dataframe