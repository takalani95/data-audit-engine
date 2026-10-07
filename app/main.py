from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# =========================================================
# PROJECT PATH
# =========================================================
# Streamlit may execute app/main.py with the app directory
# as the import root. Explicitly add the repository root so
# the local src package can always be imported.

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.ingestion.loader import (
    DatasetLoadError,
    load_dataset,
)
from src.ingestion.validators import (
    FileValidationError,
)
from src.profiling.profiler import (
    profile_dataset,
)
from src.quality.engine import (
    run_quality_audit,
)
from src.recommendations.engine import (
    generate_recommendations,
)
from src.reporting.builder import (
    build_audit_report,
)
from src.reporting.pdf_renderer import (
    render_audit_report_pdf,
)
from src.visualization.dataframe_utils import (
    make_dataframe_display_safe,
)


# =========================================================
# CONSTANTS
# =========================================================

MIDDLE_DOT = "\u00b7"


# =========================================================
# HELPERS
# =========================================================

def build_pdf_file_name(
    source_file_name: str,
) -> str:
    """
    Build a safe, predictable PDF download filename from
    the uploaded dataset name.
    """

    source_path = Path(source_file_name)

    stem = source_path.stem.strip()

    if not stem:
        stem = "dataset"

    safe_stem = "".join(
        character
        if character.isalnum()
        or character in ("-", "_")
        else "_"
        for character in stem
    )

    safe_stem = safe_stem.strip("_")

    if not safe_stem:
        safe_stem = "dataset"

    return (
        f"{safe_stem}_"
        "MASH_LABS_Data_Quality_Audit.pdf"
    )


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="MASH LABS | Data Audit Engine",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# HEADER
# =========================================================

st.title("MASH LABS")

st.caption(
    f"APPLIED AI {MIDDLE_DOT} "
    f"DATA {MIDDLE_DOT} ENGINEERING"
)

st.header("Data Audit Engine")

st.write(
    """
    Upload your data. Understand its structure, quality,
    statistics, risks and opportunities.
    """
)


# =========================================================
# FILE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a dataset",
    type=["csv", "xlsx"],
)


if uploaded_file is not None:

    try:

        # =================================================
        # INGESTION
        # =================================================

        result = load_dataset(
            file=uploaded_file,
            file_name=uploaded_file.name,
        )

        dataframe = result.dataframe
        metadata = result.metadata

        st.success(
            "Dataset successfully ingested."
        )

        # =================================================
        # PROFILING
        # =================================================

        profile = profile_dataset(
            dataframe
        )

        # =================================================
        # QUALITY AUDIT
        # =================================================

        quality_report = run_quality_audit(
            dataframe,
            profile,
        )

        # =================================================
        # RECOMMENDATIONS ENGINE
        # =================================================

        recommendations = generate_recommendations(
            quality_report
        )

        # =================================================
        # REPORTING ENGINE
        # =================================================
        # The report is assembled from the same verified
        # objects already used by the Streamlit interface.
        # No separate audit is performed for PDF export.

        audit_report = build_audit_report(
            metadata=metadata,
            profile=profile,
            quality_report=quality_report,
            recommendations=recommendations,
        )

        pdf_bytes = render_audit_report_pdf(
            audit_report
        )

        pdf_file_name = build_pdf_file_name(
            metadata.file_name
        )

        # =================================================
        # DATASET OVERVIEW
        # =================================================

        st.subheader("Dataset Overview")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Rows",
                f"{profile.rows:,}",
            )

        with col2:

            st.metric(
                "Columns",
                f"{profile.columns:,}",
            )

        with col3:

            st.metric(
                "Missing Cells",
                f"{profile.missing_cells:,}",
                help=(
                    f"{profile.missing_percentage:.2f}% "
                    "of all dataset cells"
                ),
            )

        with col4:

            st.metric(
                "Duplicate Rows",
                f"{profile.duplicate_rows:,}",
                help=(
                    f"{profile.duplicate_percentage:.2f}% "
                    "of all dataset rows"
                ),
            )

        st.caption(
            f"{metadata.file_name} {MIDDLE_DOT} "
            f"{metadata.file_type.upper()} {MIDDLE_DOT} "
            f"{metadata.file_size_bytes / 1024:.1f} KB"
        )

        # =================================================
        # QUALITY SCORE
        # =================================================

        st.divider()

        st.subheader(
            "Data Quality Assessment"
        )

        score_col, status_col, critical_col, warning_col = (
            st.columns(4)
        )

        with score_col:

            st.metric(
                "Quality Score",
                (
                    f"{quality_report.overall_score:.1f} "
                    "/ 100"
                ),
            )

        status_display = {
            "good": "GOOD",
            "needs_attention": "NEEDS ATTENTION",
            "critical": "CRITICAL",
        }

        with status_col:

            st.metric(
                "Status",
                status_display.get(
                    quality_report.status,
                    quality_report.status.upper(),
                ),
            )

        with critical_col:

            st.metric(
                "Critical Issues",
                quality_report.critical_count,
            )

        with warning_col:

            st.metric(
                "Warnings",
                quality_report.warning_count,
            )

        st.caption(
            "The quality score combines six deterministic, "
            "explainable quality dimensions using the "
            "configured weights shown below."
        )

        # =================================================
        # PDF REPORT DOWNLOAD
        # =================================================

        st.write(
            "### Audit Report"
        )

        report_col1, report_col2 = st.columns(
            [1, 2]
        )

        with report_col1:

            st.download_button(
                label="Download PDF Audit Report",
                data=pdf_bytes,
                file_name=pdf_file_name,
                mime="application/pdf",
                width="stretch",
            )

        with report_col2:

            st.caption(
                "The PDF is generated from the same "
                "deterministic audit results shown in "
                "this application. Downloading the report "
                "does not modify your source dataset."
            )

        # =================================================
        # QUALITY DIMENSIONS
        # =================================================

        st.write(
            "### Quality Dimensions"
        )

        dimension_rows = []

        display_names = {
            "completeness":
                "Completeness",

            "uniqueness":
                "Uniqueness",

            "validity":
                "Validity",

            "consistency":
                "Consistency",

            "structural_quality":
                "Structural Quality",

            "statistical_health":
                "Statistical Health",
        }

        for name, dimension in (
            quality_report.dimensions.items()
        ):

            dimension_rows.append(
                {
                    "Dimension":
                        display_names.get(
                            name,
                            name,
                        ),

                    "Score":
                        (
                            f"{dimension.score:.1f}"
                            if dimension.assessed
                            and dimension.score
                            is not None
                            else "Not Assessed"
                        ),

                    "Configured Weight":
                        f"{dimension.weight:.0f}%",

                    "Status":
                        (
                            "Assessed"
                            if dimension.assessed
                            else "Pending"
                        ),

                    "Issues":
                        len(
                            dimension.issues
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                dimension_rows
            ),
            hide_index=True,
            width="stretch",
        )

        # =================================================
        # QUALITY FINDINGS
        # =================================================

        st.write(
            "### Quality Findings"
        )

        if not quality_report.issues:

            st.success(
                "No quality issues were detected by "
                "the current audit checks."
            )

        else:

            severity_order = {
                "critical": 0,
                "warning": 1,
                "info": 2,
            }

            sorted_issues = sorted(
                quality_report.issues,
                key=lambda issue: (
                    severity_order.get(
                        issue.severity,
                        99,
                    ),
                    issue.category,
                    issue.column or "",
                ),
            )

            for issue in sorted_issues:

                heading = (
                    f"{issue.severity.upper()} "
                    f"{MIDDLE_DOT} "
                    f"{issue.title}"
                )

                if issue.column:

                    heading += (
                        f" {MIDDLE_DOT} "
                        f"{issue.column}"
                    )

                if issue.severity == "critical":

                    st.error(
                        f"**{heading}**\n\n"
                        f"{issue.description}"
                    )

                elif issue.severity == "warning":

                    st.warning(
                        f"**{heading}**\n\n"
                        f"{issue.description}"
                    )

                else:

                    st.info(
                        f"**{heading}**\n\n"
                        f"{issue.description}"
                    )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        st.divider()

        st.subheader(
            "Recommendations"
        )

        st.caption(
            "Recommendations are generated "
            "deterministically from verified quality "
            "findings. The engine does not modify "
            "your dataset automatically."
        )

        if not recommendations:

            st.success(
                "No recommendations are required from "
                "the currently detected quality findings."
            )

        else:

            high_priority = [
                recommendation
                for recommendation in recommendations
                if recommendation.priority == "high"
            ]

            medium_priority = [
                recommendation
                for recommendation in recommendations
                if recommendation.priority == "medium"
            ]

            low_priority = [
                recommendation
                for recommendation in recommendations
                if recommendation.priority == "low"
            ]

            rec_col1, rec_col2, rec_col3, rec_col4 = (
                st.columns(4)
            )

            with rec_col1:

                st.metric(
                    "Recommendations",
                    len(recommendations),
                )

            with rec_col2:

                st.metric(
                    "High Priority",
                    len(high_priority),
                )

            with rec_col3:

                st.metric(
                    "Medium Priority",
                    len(medium_priority),
                )

            with rec_col4:

                st.metric(
                    "Low Priority",
                    len(low_priority),
                )

            priority_labels = {
                "high": "HIGH PRIORITY",
                "medium": "MEDIUM PRIORITY",
                "low": "LOW PRIORITY",
            }

            for priority in (
                "high",
                "medium",
                "low",
            ):

                priority_recommendations = [
                    recommendation
                    for recommendation
                    in recommendations
                    if recommendation.priority
                    == priority
                ]

                if not priority_recommendations:
                    continue

                st.write(
                    f"### {priority_labels[priority]}"
                )

                for recommendation in (
                    priority_recommendations
                ):

                    heading = (
                        recommendation.title
                    )

                    if recommendation.column:

                        heading += (
                            f" {MIDDLE_DOT} "
                            f"{recommendation.column}"
                        )

                    affected_text = ""

                    if (
                        recommendation.affected_count
                        > 0
                    ):

                        affected_text = (
                            f"{recommendation.affected_count:,} "
                            "affected"
                        )

                        if (
                            recommendation
                            .affected_percentage
                            > 0
                        ):

                            affected_text += (
                                f" {MIDDLE_DOT} "
                                f"{recommendation.affected_percentage:.2f}%"
                            )

                    with st.expander(
                        heading,
                        expanded=(
                            priority == "high"
                        ),
                    ):

                        if affected_text:

                            st.caption(
                                affected_text
                            )

                        st.write(
                            "**Problem**"
                        )

                        st.write(
                            recommendation.problem
                        )

                        st.write(
                            "**Why it matters**"
                        )

                        st.write(
                            recommendation.why_it_matters
                        )

                        st.write(
                            "**Recommended action**"
                        )

                        st.write(
                            recommendation.recommended_action
                        )

                        st.caption(
                            "Source finding: "
                            f"{recommendation.source_issue_code}"
                        )

        # =================================================
        # DETECTED TYPES
        # =================================================

        st.divider()

        st.subheader(
            "Detected Column Types"
        )

        type_dataframe = pd.DataFrame(
            [
                {
                    "Type":
                        semantic_type.title(),

                    "Columns":
                        count,
                }
                for semantic_type, count
                in profile.type_counts.items()
            ]
        )

        type_col1, type_col2 = st.columns(
            [1, 2]
        )

        with type_col1:

            st.dataframe(
                type_dataframe,
                hide_index=True,
                width="stretch",
            )

        with type_col2:

            if not type_dataframe.empty:

                st.bar_chart(
                    type_dataframe.set_index(
                        "Type"
                    )
                )

        # =================================================
        # COLUMN PROFILE
        # =================================================

        st.subheader(
            "Column Profile"
        )

        column_rows = []

        for column in profile.column_profiles:

            column_rows.append(
                {
                    "Column":
                        column.name,

                    "Detected Type":
                        column.semantic_type.title(),

                    "Pandas Type":
                        column.pandas_dtype,

                    "Missing":
                        column.missing_count,

                    "Missing %":
                        column.missing_percentage,

                    "Unique":
                        column.unique_count,

                    "Unique %":
                        column.unique_percentage,

                    "Possible ID":
                        (
                            "Yes"
                            if column.is_possible_identifier
                            else "No"
                        ),

                    "Constant":
                        (
                            "Yes"
                            if column.is_constant
                            else "No"
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(
                column_rows
            ),
            hide_index=True,
            width="stretch",
        )

        # =================================================
        # STRUCTURAL DETAILS
        # =================================================

        with st.expander(
            "Structural Details"
        ):

            st.write(
                "**Possible Identifier Columns**"
            )

            if profile.possible_identifier_columns:

                st.write(
                    ", ".join(
                        profile.possible_identifier_columns
                    )
                )

            else:

                st.write(
                    "None detected."
                )

            st.write(
                "**Constant Columns**"
            )

            if profile.constant_columns:

                st.write(
                    ", ".join(
                        profile.constant_columns
                    )
                )

            else:

                st.write(
                    "None detected."
                )

            st.write(
                "**Unnamed Columns**"
            )

            if profile.unnamed_columns:

                st.write(
                    ", ".join(
                        profile.unnamed_columns
                    )
                )

                st.warning(
                    """
                    Unnamed columns may indicate blank
                    header cells or that the wrong row
                    was interpreted as the table header.
                    """
                )

            else:

                st.write(
                    "None detected."
                )

        # =================================================
        # COLUMN INSPECTOR
        # =================================================

        st.subheader(
            "Column Inspector"
        )

        selected_column_name = st.selectbox(
            "Select a column",
            options=[
                column.name
                for column
                in profile.column_profiles
            ],
        )

        selected_profile = next(
            column
            for column in profile.column_profiles
            if column.name
            == selected_column_name
        )

        inspect1, inspect2, inspect3, inspect4 = (
            st.columns(4)
        )

        with inspect1:

            st.metric(
                "Detected Type",
                selected_profile.semantic_type.title(),
            )

        with inspect2:

            st.metric(
                "Missing",
                (
                    f"{selected_profile.missing_percentage:.2f}%"
                ),
            )

        with inspect3:

            st.metric(
                "Unique Values",
                (
                    f"{selected_profile.unique_count:,}"
                ),
            )

        with inspect4:

            st.metric(
                "Unique %",
                (
                    f"{selected_profile.unique_percentage:.2f}%"
                ),
            )

        if (
            selected_profile.semantic_type
            == "numeric"
        ):

            st.write(
                "#### Numerical Statistics"
            )

            num1, num2, num3, num4 = (
                st.columns(4)
            )

            with num1:

                st.metric(
                    "Minimum",
                    selected_profile.minimum,
                )

            with num2:

                st.metric(
                    "Maximum",
                    selected_profile.maximum,
                )

            with num3:

                st.metric(
                    "Mean",
                    (
                        f"{selected_profile.mean:.2f}"
                        if selected_profile.mean
                        is not None
                        else "N/A"
                    ),
                )

            with num4:

                st.metric(
                    "Median",
                    (
                        f"{selected_profile.median:.2f}"
                        if selected_profile.median
                        is not None
                        else "N/A"
                    ),
                )

        st.write(
            "#### Sample Values"
        )

        if selected_profile.sample_values:

            sample_dataframe = pd.DataFrame(
                {
                    "Sample Value":
                        selected_profile.sample_values
                }
            )

            safe_sample_dataframe = (
                make_dataframe_display_safe(
                    sample_dataframe
                )
            )

            st.dataframe(
                safe_sample_dataframe,
                hide_index=True,
                width="stretch",
            )

        else:

            st.write(
                "No non-null sample values."
            )

        # =================================================
        # RAW DATA
        # =================================================

        with st.expander(
            "Raw Data Preview"
        ):

            preview_dataframe = (
                make_dataframe_display_safe(
                    dataframe.head(20)
                )
            )

            st.dataframe(
                preview_dataframe,
                width="stretch",
            )

            st.caption(
                "Showing the first 20 rows. "
                "Display-safe conversion is applied only "
                "to the preview; the audit uses the "
                "original dataset."
            )

    except FileValidationError as exc:

        st.error(
            f"File validation failed: {exc}"
        )

    except DatasetLoadError as exc:

        st.error(
            f"Dataset could not be loaded: {exc}"
        )

    except Exception as exc:

        st.error(
            "An unexpected error occurred while "
            "processing the dataset."
        )

        with st.expander(
            "Technical Details"
        ):

            st.code(
                str(exc)
            )