
from __future__ import annotations

from typing import Any

import pandas as pd


SUPPORTED_FREQUENCIES = {
    "daily",
    "weekly",
    "monthly",
    "hourly",
}


def analyse_time_series(
    series: pd.Series,
    frequency: str = "daily",
) -> dict[str, Any]:
    """
    Count observations by day, week, month or hour.

    Weekly periods start on Monday.
    Invalid and missing timestamps are excluded.
    Timezone-aware inputs are aggregated in their
    original timezone.

    The source series is never modified.
    """

    if not isinstance(series, pd.Series):
        raise TypeError("Expected a pandas Series")

    if frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError(
            "Unsupported frequency. Choose daily, "
            "weekly, monthly or hourly."
        )

    try:
        dates = pd.to_datetime(
            series,
            errors="coerce",
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Unable to parse datetime values."
        ) from exc

    if not isinstance(
        dates.dtype,
        (pd.DatetimeTZDtype, pd.DatetimeTZDtype)
    ):
        if not pd.api.types.is_datetime64_any_dtype(
            dates.dtype
        ):
            raise ValueError(
                "Mixed timezone formats are not supported."
            )

    valid = dates.dropna()

    result: dict[str, Any] = {
        "column": str(series.name),
        "frequency": frequency,
        "total_rows": len(series),
        "valid_count": len(valid),
        "missing_or_invalid_count": (
            len(series) - len(valid)
        ),
        "start_date": None,
        "end_date": None,
        "periods": [],
    }

    if valid.empty:
        return result

    result["start_date"] = valid.min().isoformat()
    result["end_date"] = valid.max().isoformat()

    if frequency == "weekly":
        # Monday-start weeks, represented by Monday.
        # Local calendar dates are used for grouping.
        local_dates = valid.dt.tz_localize(None)
        grouped = (
            local_dates.dt.to_period("W-SUN")
            .value_counts()
            .sort_index()
        )

        periods = [
            {
                "period": period.start_time.isoformat(),
                "count": int(count),
            }
            for period, count in grouped.items()
        ]

    else:
        local_dates = valid.dt.tz_localize(None)

        if frequency == "hourly":
            buckets = local_dates.dt.floor("h")
        elif frequency == "daily":
            buckets = local_dates.dt.normalize()
        else:
            buckets = (
                local_dates.dt.to_period("M")
                .dt.to_timestamp()
            )

        counts = buckets.value_counts().sort_index()

        periods = [
            {
                "period": timestamp.isoformat(),
                "count": int(count),
            }
            for timestamp, count in counts.items()
        ]

    result["periods"] = periods

    return result
