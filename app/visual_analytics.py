
from __future__ import annotations

import pandas as pd
import streamlit as st
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from src.visualization.chart_selector import select_chart
from src.visualization.dataset_intelligence import analyse_dataset_intelligence
from src.visualization.duration_charts import create_duration_histogram
from src.visualization.duration_intelligence import analyse_duration_column
from src.visualization.correlations import analyse_correlations
from src.visualization.distributions import (
    analyse_categorical_distribution,
    analyse_numeric_distribution,
)
from src.visualization.missingness import analyse_missingness
from src.visualization.plotly_renderer import render_chart
from src.visualization.time_series import analyse_time_series


def render_visual_analytics(dataframe: pd.DataFrame) -> None:
    """
    Render interactive exploratory analytics for a dataset.

    This component does not change the source dataframe
    or the existing data quality audit results.
    """

    st.divider()
    st.header("Visual Analytics")

    st.caption(
        "Explore distributions, correlations, missing "
        "data and time trends using deterministic calculations."
    )

    if dataframe.empty or len(dataframe.columns) == 0:
        st.info("No data is available for visualization.")
        return

    if not dataframe.columns.is_unique:
        st.warning(
            "Visual analytics requires unique column names."
        )
        return

    numeric_columns = [
        column
        for column in dataframe.columns
        if (
            is_numeric_dtype(dataframe[column])
            and not is_bool_dtype(dataframe[column])
        )
    ]

    categorical_columns = [
        column
        for column in dataframe.columns
        if column not in numeric_columns
    ]

    distribution_tab, correlation_tab, missing_tab, trends_tab, recommendations_tab = st.tabs(
        [
            "Distributions",
            "Correlations",
            "Missing Data",
            "Trends",
            "Recommendations",
        ]
    )

    # =====================================================
    # DISTRIBUTIONS
    # =====================================================

    with distribution_tab:
        st.subheader("Column Distributions")

        analysis_type = st.radio(
            "Distribution type",
            ["Numeric", "Categorical"],
            horizontal=True,
            key="visual_distribution_type",
        )

        if analysis_type == "Numeric":
            if not numeric_columns:
                st.info(
                    "No numeric columns are available."
                )
            else:
                selected_column = st.selectbox(
                    "Select a numeric column",
                    numeric_columns,
                    key="visual_numeric_column",
                )

                bins = st.slider(
                    "Histogram bins",
                    min_value=5,
                    max_value=100,
                    value=20,
                    key="visual_histogram_bins",
                )

                result = analyse_numeric_distribution(
                    dataframe[selected_column],
                    bins=bins,
                )

                chart_spec = select_chart(
                    "numeric_distribution",
                    result,
                )

                figure = render_chart(chart_spec)

                st.plotly_chart(
                    figure,
                    width="stretch",
                )

                metric1, metric2, metric3 = st.columns(3)

                with metric1:
                    st.metric(
                        "Valid Values",
                        f"{result['valid_count']:,}",
                    )

                with metric2:
                    st.metric(
                        "Missing Values",
                        f"{result['missing_count']:,}",
                    )

                with metric3:
                    st.metric(
                        "Non-finite Values",
                        f"{result['non_finite_count']:,}",
                    )

                st.caption(
                    "Histogram bins are calculated by the "
                    "analysis engine. Missing and infinite "
                    "values are excluded from the histogram."
                )

        else:
            if not categorical_columns:
                st.info(
                    "No categorical columns are available."
                )
            else:
                selected_column = st.selectbox(
                    "Select a categorical column",
                    categorical_columns,
                    key="visual_categorical_column",
                )

                top_n = st.slider(
                    "Maximum categories",
                    min_value=5,
                    max_value=30,
                    value=15,
                    key="visual_category_limit",
                )

                result = analyse_categorical_distribution(
                    dataframe[selected_column],
                    top_n=top_n,
                )

                chart_spec = select_chart(
                    "categorical_distribution",
                    result,
                )

                st.plotly_chart(
                    render_chart(chart_spec),
                    width="stretch",
                )

                st.metric(
                    "Unique Categories",
                    f"{result['unique_count']:,}",
                )

                if result["other_categories_count"] > 0:
                    st.caption(
                        f"{result['other_categories_count']:,} "
                        "additional categories are not shown."
                    )

    # =====================================================
    # CORRELATIONS
    # =====================================================

    with correlation_tab:
        st.subheader("Correlation Analysis")

        if len(numeric_columns) < 2:
            st.info(
                "At least two numeric columns are required "
                "for correlation analysis."
            )
        else:
            method = st.selectbox(
                "Correlation method",
                ["pearson", "spearman"],
                format_func=lambda value: value.title(),
                key="visual_correlation_method",
            )

            min_pairs = st.number_input(
                "Minimum paired observations",
                min_value=3,
                max_value=1000,
                value=8,
                step=1,
                key="visual_correlation_min_pairs",
            )

            excluded_columns = st.multiselect(
                "Exclude columns from correlation analysis",
                options=numeric_columns,
                help=(
                    "Exclude numeric identifiers or other "
                    "columns that should not be interpreted "
                    "as continuous measurements."
                ),
                key="visual_correlation_exclusions",
            )

            result = analyse_correlations(
                dataframe,
                method=method,
                min_pairs=int(min_pairs),
                excluded_columns=excluded_columns,
            )

            if not result["pairs"]:
                st.info(
                    "Select at least two numeric columns "
                    "after exclusions."
                )
            else:
                chart_spec = select_chart(
                    "correlation",
                    result,
                )

                st.plotly_chart(
                    render_chart(chart_spec),
                    width="stretch",
                )

                metric1, metric2 = st.columns(2)

                with metric1:
                    st.metric(
                        "Assessed Pairs",
                        result["assessed_pairs"],
                    )

                with metric2:
                    st.metric(
                        "Unassessed Pairs",
                        result["unassessed_pairs"],
                    )

                st.dataframe(
                    pd.DataFrame(result["pairs"]),
                    hide_index=True,
                    width="stretch",
                )

                st.caption(
                    "Correlation does not imply causation. "
                    "Pairs with insufficient observations "
                    "or constant values are not assessed."
                )

    # =====================================================
    # MISSING DATA
    # =====================================================

    with missing_tab:
        st.subheader("Missing Data Analysis")

        result = analyse_missingness(dataframe)

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric(
                "Missing Cells",
                f"{result['missing_cells']:,}",
            )

        with metric2:
            st.metric(
                "Missing Percentage",
                f"{result['missing_percentage']:.2f}%",
            )

        with metric3:
            st.metric(
                "Incomplete Rows",
                f"{result['incomplete_rows']:,}",
            )

        chart_spec = select_chart(
            "missingness",
            result,
        )

        st.plotly_chart(
            render_chart(chart_spec),
            width="stretch",
        )

        st.dataframe(
            pd.DataFrame(result["columns"]),
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Missingness uses pandas missing-value semantics. "
            "Blank strings are not counted as missing values "
            "by this analysis."
        )


    # =====================================================
    # TIME TRENDS
    # =====================================================

    with trends_tab:
        st.subheader("Time-Series Analysis")

        st.caption(
            "Analyze how record volumes change over time. "
            "Select a date column and aggregation frequency."
        )

        candidate_columns = [
            column
            for column in dataframe.columns
            if (
                pd.api.types.is_datetime64_any_dtype(
                    dataframe[column]
                )
                or (
                    not is_numeric_dtype(dataframe[column])
                    and not is_bool_dtype(dataframe[column])
                )
            )
        ]

        if not candidate_columns:
            st.info(
                "No potential datetime columns are available."
            )
        else:
            preferred_columns = [
                column
                for column in candidate_columns
                if any(
                    keyword in str(column).lower()
                    for keyword in (
                        "date",
                        "time",
                        "timestamp",
                        "created",
                        "received",
                    )
                )
            ]

            default_column = (
                preferred_columns[0]
                if preferred_columns
                else candidate_columns[0]
            )

            selected_date_column = st.selectbox(
                "Select a date or timestamp column",
                candidate_columns,
                index=candidate_columns.index(default_column),
                key="visual_trend_date_column",
            )

            frequency = st.selectbox(
                "Aggregation frequency",
                ["daily", "weekly", "monthly", "hourly"],
                format_func=lambda value: value.title(),
                key="visual_trend_frequency",
            )

            try:
                result = analyse_time_series(
                    dataframe[selected_date_column],
                    frequency=frequency,
                )

                if result["valid_count"] == 0:
                    st.warning(
                        "No valid timestamps were found in "
                        "the selected column."
                    )
                else:
                    chart_spec = select_chart(
                        "time_series",
                        result,
                    )

                    figure = render_chart(chart_spec)

                    st.plotly_chart(
                        figure,
                        width="stretch",
                    )

                    metric1, metric2, metric3 = st.columns(3)

                    with metric1:
                        st.metric(
                            "Valid Timestamps",
                            f"{result['valid_count']:,}",
                        )

                    with metric2:
                        st.metric(
                            "Invalid / Missing",
                            (
                                f"{result['missing_or_invalid_count']:,}"
                            ),
                        )

                    with metric3:
                        st.metric(
                            "Observed Periods",
                            f"{len(result['periods']):,}",
                        )

                    st.dataframe(
                        pd.DataFrame(result["periods"]),
                        hide_index=True,
                        width="stretch",
                    )

                    st.caption(
                        "Counts represent records per period. "
                        "Missing and invalid dates are excluded. "
                        "Periods without records are not shown."
                    )

            except (ValueError, TypeError) as exc:
                st.warning(
                    f"Unable to analyze this date column: {exc}"
                )


    # =====================================================
    # INTELLIGENT CHART RECOMMENDATIONS
    # =====================================================

    with recommendations_tab:
        st.subheader("Intelligent Chart Recommendations")

        st.caption(
            "MASH LABS examines each column and suggests "
            "a suitable visualization using deterministic "
            "data-type and cardinality rules."
        )

        intelligence = analyse_dataset_intelligence(dataframe)

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric(
                "Columns Analysed",
                intelligence["column_count"],
            )

        with metric2:
            st.metric(
                "Charts Recommended",
                intelligence["recommended_count"],
            )

        with metric3:
            st.metric(
                "Columns Skipped",
                intelligence["skipped_count"],
            )

        recommendation_rows = []

        for item in intelligence["columns"]:
            recommendation_rows.append({
                "Column": item["column"],
                "Position": item["column_index"] + 1,
                "Detected Type": item["semantic_type"],
                "Recommended Chart": (
                    item["recommended_chart"] or "None"
                ),
                "Unique Values": item["unique_count"],
                "Missing Values": item["missing_count"],
                "Explanation": item["reason"],
            })

        st.dataframe(
            pd.DataFrame(recommendation_rows),
            hide_index=True,
            width="stretch",
        )


        # Duration Intelligence preview
        duration_columns = [
            item["column"]
            for item in intelligence["columns"]
            if item["semantic_type"] == "duration"
        ]

        if duration_columns:
            st.divider()
            st.subheader("Duration Intelligence")

            selected_duration = st.selectbox(
                "Select a duration column",
                duration_columns,
                key="visual_recommended_duration",
            )

            duration_bins = st.slider(
                "Duration histogram bins",
                min_value=5,
                max_value=100,
                value=30,
                key="visual_duration_bins",
            )

            duration_result = analyse_duration_column(
                dataframe[selected_duration]
            )

            if duration_result["valid_count"] > 0:
                duration_figure = create_duration_histogram(
                    dataframe[selected_duration],
                    bins=duration_bins,
                )

                st.plotly_chart(
                    duration_figure,
                    width="stretch",
                )

                d1, d2, d3, d4 = st.columns(4)

                with d1:
                    st.metric(
                        "Valid Durations",
                        f"{duration_result['valid_count']:,}",
                    )

                with d2:
                    st.metric(
                        "Invalid / Missing",
                        f"{duration_result['invalid_or_missing_count']:,}",
                    )

                with d3:
                    st.metric(
                        "Median (minutes)",
                        f"{duration_result['median']:,.1f}",
                    )

                with d4:
                    st.metric(
                        "Parse Success",
                        f"{duration_result['parse_success_rate']:.2%}",
                    )

                st.caption(
                    "Durations are converted to minutes. "
                    "Unrecognised values are excluded from "
                    "the histogram and counted separately."
                )
            else:
                st.warning(
                    "No valid durations are available "
                    "for this column."
                )

        st.caption(
            "Recommendations are heuristic and may require "
            "business-context review. Identifier columns are "
            "not automatically charted."
        )
