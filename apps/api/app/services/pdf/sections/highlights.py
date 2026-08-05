"""
PDF rendering: trip highlights page.
"""
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Spacer, Table, TableStyle

from app.schemas.trip import TripRequest
from app.services.pdf.constants import COLORS, PAGE_INNER_WIDTH
from app.services.pdf.highlight_builder import highlight_sections
from app.services.pdf.text_utils import escape_text


def render_highlights_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, itinerary_text: str) -> None:
    sections = highlight_sections(itinerary_text, request)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("TRIP HIGHLIGHTS", styles["highlights_title"]))
    story.append(Paragraph("A data-driven overview of the selected guest journey.", styles["highlights_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.18 * inch))

    card_width = (PAGE_INNER_WIDTH - 12) / 2
    rows = []
    for index in range(0, len(sections), 2):
        row = []
        for section in sections[index: index + 2]:
            content = [
                Paragraph(escape_text(section["title"]), styles["highlight_heading"]),
                Paragraph(escape_text(section["value"]), styles["highlight_value"]),
                Paragraph(escape_text(section["description"]), styles["highlight_body"]),
            ]
            row.append(content)
        if len(row) == 1:
            row.append("")
        rows.append(row)

    table = Table(rows, colWidths=[card_width, card_width], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["card"]),
        ("BOX", (0, 0), (-1, -1), 0.7, COLORS["line"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [COLORS["card"], COLORS["soft_white"]]),
    ]))
    story.append(table)
    story.append(PageBreak())
