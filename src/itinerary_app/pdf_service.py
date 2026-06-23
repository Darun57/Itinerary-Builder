from io import BytesIO
from pathlib import Path
import re

from PIL import Image as PILImage
from PIL import ImageDraw
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from itinerary_app.config import BRAND_NAME
from itinerary_app.image_loader import get_destination_image_path, get_hotel_image_path
from itinerary_app.models import TripRequest
from itinerary_app.recommendations import recommend_hotels
from itinerary_app.data_loader import load_destinations


COLORS = {
    "navy": colors.HexColor("#0f1c2e"),
    "gold": colors.HexColor("#c8a96a"),
    "white": colors.HexColor("#ffffff"),
    "soft_white": colors.HexColor("#f8fafc"),
    "soft_grey": colors.HexColor("#64748b"),
    "line": colors.HexColor("#d6c29b"),
    "body": colors.HexColor("#334155"),
    "dark": colors.HexColor("#10202d"),
    "card": colors.HexColor("#fbfaf7"),
}
MARGINS = {"left": 52, "right": 52, "top": 40, "bottom": 42}
SPACING = {"xs": 0.05 * inch, "sm": 0.1 * inch, "md": 0.18 * inch, "lg": 0.28 * inch, "xl": 0.45 * inch}
PAGE_WIDTH, PAGE_HEIGHT = A4
PAGE_INNER_WIDTH = PAGE_WIDTH - MARGINS["left"] - MARGINS["right"]
FONT_DIRS = [
    Path(__file__).resolve().parents[2] / "assets" / "fonts",
    Path(__file__).resolve().parents[2] / "fonts",
]
FONT_CANDIDATES = {
    "heading": ["PlayfairDisplay-Bold.ttf", "CormorantGaramond-Bold.ttf", "Times-Bold"],
    "subheading": ["PlayfairDisplay-SemiBold.ttf", "CormorantGaramond-SemiBold.ttf", "Helvetica-Bold"],
    "body": ["CormorantGaramond-Regular.ttf", "SourceSans3-Regular.ttf", "Helvetica"],
    "body_bold": ["CormorantGaramond-SemiBold.ttf", "SourceSans3-SemiBold.ttf", "Helvetica-Bold"],
}
SECTION_LABELS = {"morning", "afternoon", "evening", "overnight stay"}
ITINERARY_KEYWORDS = {
    "cellular jail light and sound show": "Cellular Jail Light & Sound Show",
    "radhanagar beach sunset": "Radhanagar Beach Sunset",
    "scuba diving": "Scuba Diving Experience",
    "natural bridge": "Natural Bridge Visit",
    "glass bottom boat": "Glass Bottom Boat Ride",
    "north bay": "North Bay and Ross Island",
    "ross island": "North Bay and Ross Island",
}


def _load_font(font_name: str, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate.endswith(".ttf"):
            for directory in FONT_DIRS:
                path = directory / candidate
                if path.exists():
                    registered_name = f"{font_name}-{path.stem}"
                    try:
                        pdfmetrics.registerFont(TTFont(registered_name, str(path)))
                        return registered_name
                    except Exception:
                        continue
        else:
            return candidate
    return "Helvetica"


def _font_map() -> dict[str, str]:
    return {
        "heading": _load_font("heading", FONT_CANDIDATES["heading"]),
        "subheading": _load_font("subheading", FONT_CANDIDATES["subheading"]),
        "body": _load_font("body", FONT_CANDIDATES["body"]),
        "body_bold": _load_font("body_bold", FONT_CANDIDATES["body_bold"]),
    }


def _build_cover_image() -> BytesIO:
    width, height = 1600, 900
    image = PILImage.new("RGB", (width, height), "#0c1720")
    draw = ImageDraw.Draw(image)
    for index in range(height):
        ratio = index / max(height - 1, 1)
        red = int(12 + (31 - 12) * ratio)
        green = int(23 + (61 - 23) * ratio)
        blue = int(32 + (89 - 32) * ratio)
        draw.line((0, index, width, index), fill=(red, green, blue))
    draw.ellipse((90, 80, 600, 590), fill=(214, 190, 145))
    draw.polygon([(0, 700), (450, 470), (900, 700)], fill=(37, 71, 82))
    draw.polygon([(520, 760), (1040, 430), (1600, 760)], fill=(24, 55, 66))
    draw.rectangle((0, 760, width, height), fill=(9, 33, 40))
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def _build_styles() -> dict[str, ParagraphStyle]:
    fonts = _font_map()
    base_styles = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle("brand", parent=base_styles["BodyText"], fontName=fonts["subheading"], fontSize=11, leading=14, alignment=TA_CENTER, textColor=COLORS["gold"], spaceAfter=8),
        "cover_title": ParagraphStyle("cover_title", parent=base_styles["Title"], fontName=fonts["heading"], fontSize=27, leading=33, alignment=TA_CENTER, textColor=COLORS["dark"], spaceAfter=10),
        "cover_subtitle": ParagraphStyle("cover_subtitle", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=11, leading=16, alignment=TA_CENTER, textColor=COLORS["soft_grey"], spaceAfter=4),
        "section_title": ParagraphStyle("section_title", parent=base_styles["Heading2"], fontName=fonts["subheading"], fontSize=15, leading=21, textColor=COLORS["dark"], spaceBefore=10, spaceAfter=8),
        "day_title": ParagraphStyle("day_title", parent=base_styles["Heading2"], fontName=fonts["heading"], fontSize=18, leading=24, textColor=COLORS["dark"], spaceBefore=4, spaceAfter=8),
        "label": ParagraphStyle("label", parent=base_styles["BodyText"], fontName=fonts["body_bold"], fontSize=10.5, leading=15, textColor=COLORS["dark"], spaceAfter=3),
        "body": ParagraphStyle("body", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=10.5, leading=15, textColor=COLORS["body"], spaceAfter=5),
        "fine": ParagraphStyle("fine", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=9.5, leading=14, textColor=COLORS["soft_grey"], spaceAfter=4),
        "highlights_title": ParagraphStyle("highlights_title", parent=base_styles["Heading2"], fontName=fonts["heading"], fontSize=21, leading=26, alignment=TA_CENTER, textColor=COLORS["dark"], spaceAfter=10),
        "highlights_subtitle": ParagraphStyle("highlights_subtitle", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=10.5, leading=15, alignment=TA_CENTER, textColor=COLORS["soft_grey"], spaceAfter=4),
        "highlight_body": ParagraphStyle("highlight_body", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=10, leading=14, textColor=COLORS["body"], leftIndent=8, spaceAfter=6),
        "hotel_name": ParagraphStyle("hotel_name", parent=base_styles["Heading3"], fontName=fonts["heading"], fontSize=15, leading=18, textColor=COLORS["gold"], spaceAfter=3),
        "hotel_meta": ParagraphStyle("hotel_meta", parent=base_styles["BodyText"], fontName=fonts["body_bold"], fontSize=10.2, leading=14, textColor=COLORS["dark"], spaceAfter=3),
        "hotel_body": ParagraphStyle("hotel_body", parent=base_styles["BodyText"], fontName=fonts["body"], fontSize=9.8, leading=13.5, textColor=COLORS["body"], spaceAfter=4),
    }


def sanitize_itinerary_text(itinerary_text: str) -> str:
    cleaned_lines = []
    for line in itinerary_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = re.sub(r"[*_`#>\[\]]", "", cleaned)
        cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:")
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def _escape_text(text: str) -> str:
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _extract_trip_title(itinerary_text: str, destination: str) -> str:
    for line in itinerary_text.splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.lower().startswith("day "):
            return cleaned
    return f"{destination} Journey"


def split_itinerary_into_days(itinerary_text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current_day: dict[str, object] | None = None
    for raw_line in itinerary_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower_line = line.lower()
        if lower_line.startswith("day "):
            current_day = {"heading": line, "items": []}
            sections.append(current_day)
            continue
        if current_day is None:
            current_day = {"heading": "Overview", "items": []}
            sections.append(current_day)
        label = ""
        content = line
        if ":" in line:
            possible_label, remainder = line.split(":", 1)
            normalized_label = possible_label.strip().lower()
            if normalized_label in SECTION_LABELS:
                label = possible_label.strip().title()
                content = remainder.strip()
        current_day["items"].append({"label": label, "content": content})
    return sections


def _extract_highlights(itinerary_text: str, request: TripRequest) -> dict[str, list[str]]:
    highlights: list[str] = []
    destinations: list[str] = []
    premium_experiences: list[str] = []
    for raw_line in itinerary_text.splitlines():
        line = raw_line.strip()
        lower_line = line.lower()
        if lower_line.startswith("day "):
            continue
        for keyword, label in ITINERARY_KEYWORDS.items():
            if keyword in lower_line and label not in highlights:
                highlights.append(label)
                break
        if "port blair" in lower_line and "Port Blair" not in destinations:
            destinations.append("Port Blair")
        if "swaraj dweep" in lower_line and "Swaraj Dweep" not in destinations:
            destinations.append("Swaraj Dweep")
        if "shaheed dweep" in lower_line and "Shaheed Dweep" not in destinations:
            destinations.append("Shaheed Dweep")
        if "baratang" in lower_line and "Baratang" not in destinations:
            destinations.append("Baratang")
        if any(term in lower_line for term in ["scuba", "sunset", "ferry", "island", "show"]):
            premium_experiences.append(line)
    if not highlights:
        highlights = ["Curated sightseeing", "Luxury island pacing", "Scenic ferry movement", "Premium leisure moments", "Guest-ready itinerary flow"]
    if not destinations:
        destinations = [request.destination or "Andaman Islands"]
    premium_experiences = premium_experiences[:5] or ["Luxury timing and destination flow"]
    return {"highlights": highlights[:5], "destinations": destinations[:5], "premium": premium_experiences[:5]}


def get_destination_image(destination: str):
    return get_destination_image_path(destination) or _build_cover_image()


def _page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(COLORS["soft_grey"])
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def render_header(canvas, doc, request: TripRequest) -> None:
    if canvas.getPageNumber() <= 1:
        return
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 9.5)
    canvas.setFillColor(COLORS["dark"])
    header_text = f"{request.customer_name} | {request.destination} | {request.number_of_days} Days"
    canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 24, header_text)
    canvas.setStrokeColor(COLORS["line"])
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, PAGE_HEIGHT - 29, PAGE_WIDTH - doc.rightMargin, PAGE_HEIGHT - 29)
    canvas.restoreState()


def render_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(COLORS["line"])
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 34, PAGE_WIDTH - doc.rightMargin, 34)
    canvas.setFont("Helvetica", 8.7)
    canvas.setFillColor(COLORS["soft_grey"])
    canvas.drawString(doc.leftMargin, 20, "Darun Tourism | Luxury Travel Specialists")
    canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def render_cover_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, trip_title: str) -> None:
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(_escape_text(BRAND_NAME), styles["brand"]))
    story.append(HRFlowable(width="16%", thickness=1.1, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Image(get_destination_image(request.destination), width=6.7 * inch, height=3.8 * inch))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(_escape_text(trip_title), styles["cover_title"]))
    story.append(Paragraph("Luxury Andaman Travel Proposal", styles["cover_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(_escape_text(f"Prepared for {request.customer_name}"), styles["cover_subtitle"]))
    story.append(Paragraph(_escape_text(f"Destination: {request.destination}"), styles["cover_subtitle"]))
    story.append(Paragraph(_escape_text(f"Duration: {request.number_of_days} Days / {request.number_of_nights} Nights"), styles["cover_subtitle"]))
    story.append(Spacer(1, 0.06 * inch))
    story.append(HRFlowable(width="28%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(PageBreak())


def render_highlights_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, itinerary_text: str) -> None:
    highlights = _extract_highlights(itinerary_text, request)
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("TRIP HIGHLIGHTS", styles["highlights_title"]))
    story.append(Paragraph("A concise overview of the key experiences shaping this luxury proposal.", styles["highlights_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("Premium Experiences", styles["section_title"]))
    for item in highlights["highlights"]:
        story.append(Paragraph(f"✓ {_escape_text(item)}", styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Destinations Covered", styles["section_title"]))
    for item in highlights["destinations"]:
        story.append(Paragraph(f"• {_escape_text(item)}", styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Number of Days and Nights", styles["section_title"]))
    story.append(Paragraph(_escape_text(f"{request.number_of_days} Days | {request.number_of_nights} Nights"), styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Top Activities", styles["section_title"]))
    for item in highlights["premium"]:
        story.append(Paragraph(f"• {_escape_text(item)}", styles["highlight_body"]))
    story.append(PageBreak())


def _hotel_stay_text(hotel_row: dict[str, object], destinations_frame) -> str:
    location = str(hotel_row.get("location") or "").strip()
    matches = destinations_frame[destinations_frame["destination_name"].str.lower() == location.lower()] if not destinations_frame.empty else None
    if matches is not None and not matches.empty:
        minimum_days = str(matches.iloc[0].get("minimum_days") or "").strip()
        maximum_days = str(matches.iloc[0].get("maximum_days") or "").strip()
        if minimum_days and maximum_days:
            return f"{minimum_days} to {maximum_days} nights"
    category = str(hotel_row.get("category") or "").strip()
    if category.lower() == "luxury":
        return "2 to 3 nights"
    if category.lower() == "premium":
        return "1 to 2 nights"
    return "1 night"


def _hotel_card_flowable(hotel_row: dict[str, object], destination_stays_frame) -> Table:
    hotel_name = str(hotel_row.get("hotel_name") or "").strip()
    location = str(hotel_row.get("location") or "").strip()
    category = str(hotel_row.get("category") or "").strip()
    description = str(hotel_row.get("description") or "").strip()
    stay_text = _hotel_stay_text(hotel_row, destination_stays_frame)
    image_path = get_hotel_image_path(hotel_name)
    image_cell: list = []
    if image_path:
        image_cell.append(Image(str(image_path), width=2.55 * inch, height=1.55 * inch))
    else:
        image_cell.append(Spacer(1, 1.55 * inch))
    details = [
        Paragraph(_escape_text(f"{hotel_name} ★★★★★"), ParagraphStyle("hotel_card_name", fontName=_font_map()["heading"], fontSize=14, leading=17, textColor=COLORS["gold"], spaceAfter=4)),
        Paragraph(_escape_text(location), ParagraphStyle("hotel_card_meta", fontName=_font_map()["body_bold"], fontSize=10.2, leading=14, textColor=COLORS["dark"], spaceAfter=3)),
        Paragraph(_escape_text(category), ParagraphStyle("hotel_card_meta2", fontName=_font_map()["body"], fontSize=9.6, leading=13, textColor=COLORS["soft_grey"], spaceAfter=4)),
        Paragraph(_escape_text(description), ParagraphStyle("hotel_card_body", fontName=_font_map()["body"], fontSize=9.6, leading=13, textColor=COLORS["body"], spaceAfter=4)),
        Paragraph(_escape_text(f"Recommended Stay: {stay_text}"), ParagraphStyle("hotel_card_stay", fontName=_font_map()["body_bold"], fontSize=9.6, leading=13, textColor=COLORS["dark"], spaceAfter=0)),
    ]
    card = Table([[image_cell[0], details]], colWidths=[2.6 * inch, 3.2 * inch])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["card"]),
                ("BOX", (0, 0), (-1, -1), 0.8, COLORS["gold"]),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, COLORS["line"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return card


def render_luxury_stays_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    hotel_frame = recommend_hotels(request)
    if hotel_frame.empty:
        return
    destinations_frame = load_destinations()
    story.append(Paragraph("YOUR LUXURY STAYS", styles["highlights_title"]))
    story.append(Paragraph("Elegant stays selected from Darun Tourism inventory.", styles["highlights_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.18 * inch))

    rows = []
    current_row = []
    for _, hotel_row in hotel_frame.iterrows():
        current_row.append(_hotel_card_flowable(hotel_row.to_dict(), destinations_frame))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        current_row.append(Spacer(1, 0.01 * inch))
        rows.append(current_row)

    table_rows = []
    for row in rows:
        if len(row) == 1:
            table_rows.append([row[0], Spacer(1, 0.01 * inch)])
        else:
            table_rows.append(row)

    if table_rows:
        grid = Table(table_rows, colWidths=[PAGE_INNER_WIDTH / 2 - 6, PAGE_INNER_WIDTH / 2 - 6], hAlign="CENTER")
        grid.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(grid)
    story.append(PageBreak())


def render_day_page(story: list, styles: dict[str, ParagraphStyle], day_section: dict[str, object], destination: str) -> None:
    heading = str(day_section["heading"])
    clean_heading = re.sub(r"^day\s*", "DAY ", heading, flags=re.IGNORECASE)
    story.append(Spacer(1, 0.04 * inch))
    story.append(Paragraph(_escape_text(clean_heading), styles["day_title"]))
    story.append(HRFlowable(width="100%", thickness=0.7, color=COLORS["line"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"Journey to {_escape_text(destination)}", styles["section_title"]))
    story.append(Spacer(1, 0.04 * inch))
    story.append(Image(get_destination_image(destination), width=6.15 * inch, height=2.55 * inch))
    story.append(Spacer(1, 0.14 * inch))
    for item in day_section["items"]:
        label = str(item["label"] or "").strip()
        content = _escape_text(str(item["content"] or "").strip())
        if label:
            story.append(Paragraph(_escape_text(label), styles["label"]))
        story.append(Paragraph(content, styles["body"]))
        story.append(Spacer(1, 0.02 * inch))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="100%", thickness=0.4, color=COLORS["soft_grey"]))
    story.append(Spacer(1, 0.04 * inch))


def render_terms_pages(story: list, styles: dict[str, ParagraphStyle]) -> None:
    story.append(PageBreak())
    sections = {
        "Inclusions": [
            "Curated day-wise itinerary planning aligned with guest preferences and destination pacing.",
            "Suggested sightseeing flow designed for a polished premium travel experience.",
            "Presentation format suitable for internal review before guest sharing.",
        ],
        "Exclusions": [
            "Flights, personal expenses, optional experiences, and any service not finally confirmed.",
            "Meals, entries, or transfers unless specifically included in the approved proposal.",
            "Supplier-driven changes arising from weather, operations, or availability constraints.",
        ],
        "Terms and Conditions": [
            "The itinerary remains subject to operational feasibility, seasonal conditions, and final service availability.",
            "Ferry timings, stay sequencing, and sightseeing flow may be refined before final confirmation.",
            "All proposal details should be reviewed internally before external circulation to guests.",
        ],
        "Contact Details": [
            "Darun Tourism",
            "Luxury Andaman itinerary planning and guest experience support",
            "Please add final operational contact details before sending to guests if required.",
        ],
    }
    for heading, lines in sections.items():
        story.append(Paragraph(_escape_text(heading), styles["section_title"]))
        story.append(HRFlowable(width="22%", thickness=1.0, color=COLORS["gold"], hAlign="LEFT"))
        story.append(Spacer(1, 0.12 * inch))
        for line in lines:
            story.append(Paragraph(_escape_text(line), styles["fine"]))
        story.append(Spacer(1, 0.14 * inch))


def generate_luxury_pdf(request: TripRequest, itinerary_text: str) -> bytes:
    buffer = BytesIO()
    styles = _build_styles()
    cleaned_itinerary = sanitize_itinerary_text(itinerary_text)
    trip_title = _extract_trip_title(cleaned_itinerary, request.destination)
    itinerary_lines = cleaned_itinerary.splitlines()
    if itinerary_lines and itinerary_lines[0].strip() == trip_title.strip():
        cleaned_itinerary = "\n".join(itinerary_lines[1:]).strip()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=MARGINS["right"],
        leftMargin=MARGINS["left"],
        topMargin=MARGINS["top"],
        bottomMargin=MARGINS["bottom"],
    )
    story: list = []
    render_cover_page(story, styles, request, trip_title)
    render_highlights_page(story, styles, request, cleaned_itinerary)
    render_luxury_stays_page(story, styles, request)
    day_sections = split_itinerary_into_days(cleaned_itinerary)
    for index, section in enumerate(day_sections):
        render_day_page(story, styles, section, destination=request.destination)
        if index != len(day_sections) - 1:
            story.append(PageBreak())
    render_terms_pages(story, styles)
    document.build(
        story,
        onFirstPage=lambda canvas, doc: render_footer(canvas, doc),
        onLaterPages=lambda canvas, doc: (render_header(canvas, doc, request), render_footer(canvas, doc)),
    )
    return buffer.getvalue()
