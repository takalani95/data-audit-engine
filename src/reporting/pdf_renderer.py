from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.reporting.models import AuditReport


BRAND_NAME = "MASH LABS"
BRAND_DESCRIPTOR = "APPLIED AI · DATA · ENGINEERING"

PRIMARY = colors.HexColor("#2858FF")
SECONDARY = colors.HexColor("#22A7E8")
DARK = colors.HexColor("#111827")
MUTED = colors.HexColor("#5F6B7A")
LIGHT = colors.HexColor("#F4F7FB")
BORDER = colors.HexColor("#D9E1EC")

CRITICAL = colors.HexColor("#B42318")
WARNING = colors.HexColor("#B54708")
GOOD = colors.HexColor("#067647")


def _safe(value: object) -> str:
    """
    Convert arbitrary report values into safe
    ReportLab paragraph text.
    """

    if value is None:
        return "—"

    return escape(str(value))


def _percentage(value: float) -> str:
    return f"{value:.2f}%"


def _score(value: float | None) -> str:
    if value is None:
        return "Not assessed"

    return f"{value:.1f}"


def _status_label(status: str) -> str:
    return status.replace("_", " ").upper()


def _status_colour(status: str):
    if status == "good":
        return GOOD

    if status == "critical":
        return CRITICAL

    return WARNING


def _priority_colour(priority: str):
    if priority == "high":
        return CRITICAL

    if priority == "medium":
        return WARNING

    return MUTED


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="MashBrand",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=DARK,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MashDescriptor",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=PRIMARY,
            tracking=1.2,
            spaceAfter=18,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=DARK,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=DARK,
            spaceBefore=10,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=DARK,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Muted",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Score",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=34,
            alignment=TA_CENTER,
            textColor=PRIMARY,
        )
    )

    return styles


def _footer(
    canvas,
    document,
) -> None:
    """
    Add a restrained MASH LABS footer to every page.
    """

    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        13 * mm,
        width - 18 * mm,
        13 * mm,
    )

    canvas.setFont(
        "Helvetica",
        7,
    )
    canvas.setFillColor(MUTED)

    canvas.drawString(
        18 * mm,
        8 * mm,
        "MASH LABS · Data Quality Audit",
    )

    canvas.drawRightString(
        width - 18 * mm,
        8 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


def _summary_table(
    report: AuditReport,
    styles,
):
    data = [
        [
            Paragraph(
                "<b>Dataset</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                _safe(report.file_name),
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>File type</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                _safe(
                    report.file_type.upper()
                ),
                styles["BodySmall"],
            ),
        ],
        [
            Paragraph(
                "<b>Rows</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                f"{report.rows:,}",
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>Columns</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                f"{report.columns:,}",
                styles["BodySmall"],
            ),
        ],
        [
            Paragraph(
                "<b>Missing cells</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                (
                    f"{report.missing_cells:,} "
                    f"({_percentage(report.missing_percentage)})"
                ),
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>Duplicate rows</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                (
                    f"{report.duplicate_rows:,} "
                    f"({_percentage(report.duplicate_percentage)})"
                ),
                styles["BodySmall"],
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=[
            31 * mm,
            55 * mm,
            31 * mm,
            55 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return table


def _quality_summary(
    report: AuditReport,
    styles,
):
    status_colour = _status_colour(
        report.quality_status
    )

    score_block = Paragraph(
        (
            f"<b>{report.quality_score:.1f}</b>"
            "<br/>"
            "<font size='8'>OUT OF 100</font>"
        ),
        styles["Score"],
    )

    status_block = Paragraph(
        (
            "<b>Operational status</b><br/>"
            f"<font color='{status_colour.hexval()}'>"
            f"<b>{_status_label(report.quality_status)}</b>"
            "</font>"
            "<br/><br/>"
            f"Critical findings: {report.critical_count}<br/>"
            f"Warnings: {report.warning_count}<br/>"
            f"Information findings: {report.info_count}"
        ),
        styles["BodySmall"],
    )

    table = Table(
        [
            [
                score_block,
                status_block,
            ]
        ],
        colWidths=[
            55 * mm,
            117 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BORDER,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
            ]
        )
    )

    return table


def _dimensions_table(
    report: AuditReport,
    styles,
):
    data = [
        [
            Paragraph(
                "<b>Dimension</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>Score</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>Weight</b>",
                styles["BodySmall"],
            ),
            Paragraph(
                "<b>Findings</b>",
                styles["BodySmall"],
            ),
        ]
    ]

    for dimension in report.dimensions:
        data.append(
            [
                Paragraph(
                    _safe(dimension.name),
                    styles["BodySmall"],
                ),
                Paragraph(
                    _score(dimension.score),
                    styles["BodySmall"],
                ),
                Paragraph(
                    f"{dimension.weight:.1f}%",
                    styles["BodySmall"],
                ),
                Paragraph(
                    str(dimension.issue_count),
                    styles["BodySmall"],
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            75 * mm,
            32 * mm,
            32 * mm,
            33 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    DARK,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    BORDER,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    return table


def _finding_block(
    finding,
    styles,
):
    severity = finding.severity.upper()

    if finding.severity == "critical":
        colour = CRITICAL
    elif finding.severity == "warning":
        colour = WARNING
    else:
        colour = MUTED

    location = ""

    if finding.column:
        location = (
            f" · {_safe(finding.column)}"
        )

    affected = ""

    if finding.affected_count:
        affected = (
            "<br/>"
            f"<b>Affected:</b> "
            f"{finding.affected_count:,} "
            f"({_percentage(finding.affected_percentage)})"
        )

    return KeepTogether(
        [
            Paragraph(
                (
                    f"<font color='{colour.hexval()}'>"
                    f"<b>{severity}</b>"
                    "</font>"
                    f" · <b>{_safe(finding.title)}</b>"
                    f"{location}"
                ),
                styles["BodySmall"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                _safe(finding.description)
                + affected,
                styles["BodySmall"],
            ),
            Spacer(1, 4 * mm),
        ]
    )


def _recommendation_block(
    recommendation,
    styles,
):
    colour = _priority_colour(
        recommendation.priority
    )

    location = ""

    if recommendation.column:
        location = (
            f" · {_safe(recommendation.column)}"
        )

    affected = ""

    if recommendation.affected_count:
        affected = (
            "<br/>"
            f"<b>Affected:</b> "
            f"{recommendation.affected_count:,} "
            f"({_percentage(recommendation.affected_percentage)})"
        )

    return KeepTogether(
        [
            Paragraph(
                (
                    f"<font color='{colour.hexval()}'>"
                    f"<b>{recommendation.priority.upper()} PRIORITY</b>"
                    "</font>"
                    f" · <b>{_safe(recommendation.title)}</b>"
                    f"{location}"
                ),
                styles["BodySmall"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                (
                    "<b>Problem:</b> "
                    f"{_safe(recommendation.problem)}"
                    f"{affected}"
                ),
                styles["BodySmall"],
            ),
            Spacer(1, 1.5 * mm),
            Paragraph(
                (
                    "<b>Why it matters:</b> "
                    f"{_safe(recommendation.why_it_matters)}"
                ),
                styles["BodySmall"],
            ),
            Spacer(1, 1.5 * mm),
            Paragraph(
                (
                    "<b>Recommended action:</b> "
                    f"{_safe(recommendation.recommended_action)}"
                ),
                styles["BodySmall"],
            ),
            Spacer(1, 5 * mm),
        ]
    )


def render_audit_report_pdf(
    report: AuditReport,
) -> bytes:
    """
    Render an AuditReport into an in-memory PDF.

    The renderer does not perform data analysis and
    does not modify the source dataset.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=report.report_title,
        author=BRAND_NAME,
        subject="Data Quality Audit",
    )

    styles = _build_styles()

    story = []

    story.append(
        Paragraph(
            BRAND_NAME,
            styles["MashBrand"],
        )
    )

    story.append(
        Paragraph(
            BRAND_DESCRIPTOR,
            styles["MashDescriptor"],
        )
    )

    story.append(
        Paragraph(
            _safe(report.report_title),
            styles["ReportTitle"],
        )
    )

    story.append(
        Paragraph(
            (
                "Deterministic assessment of dataset "
                "structure, quality, statistical health, "
                "verified findings, and recommended "
                "actions."
            ),
            styles["Muted"],
        )
    )

    story.append(
        Spacer(
            1,
            7 * mm,
        )
    )

    story.append(
        Paragraph(
            "Dataset Overview",
            styles["SectionTitle"],
        )
    )

    story.append(
        _summary_table(
            report,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "Quality Assessment",
            styles["SectionTitle"],
        )
    )

    story.append(
        _quality_summary(
            report,
            styles,
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "Quality Dimensions",
            styles["SectionTitle"],
        )
    )

    story.append(
        _dimensions_table(
            report,
            styles,
        )
    )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Verified Findings",
            styles["SectionTitle"],
        )
    )

    if report.findings:
        for finding in report.findings:
            story.append(
                _finding_block(
                    finding,
                    styles,
                )
            )
    else:
        story.append(
            Paragraph(
                (
                    "No data-quality findings were "
                    "identified by the assessed rules."
                ),
                styles["BodySmall"],
            )
        )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Recommendations",
            styles["SectionTitle"],
        )
    )

    if report.recommendations:
        for recommendation in (
            report.recommendations
        ):
            story.append(
                _recommendation_block(
                    recommendation,
                    styles,
                )
            )
    else:
        story.append(
            Paragraph(
                (
                    "No recommendations were generated "
                    "from the verified findings."
                ),
                styles["BodySmall"],
            )
        )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    story.append(
        Paragraph(
            "Methodology",
            styles["SectionTitle"],
        )
    )

    story.append(
        Paragraph(
            (
                "The MASH LABS Data Audit Engine uses "
                "deterministic and explainable rules to "
                "assess six weighted dimensions: "
                "Completeness, Uniqueness, Validity, "
                "Consistency, Structural Quality, and "
                "Statistical Health. Findings and "
                "recommendations in this report are "
                "derived from the audit results and do "
                "not modify the source dataset."
            ),
            styles["BodySmall"],
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    story.append(
        Paragraph(
            (
                "Automated findings should be interpreted "
                "together with business context. A high "
                "aggregate score does not override "
                "critical localised findings, which may "
                "still require operational attention."
            ),
            styles["Muted"],
        )
    )

    document.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes