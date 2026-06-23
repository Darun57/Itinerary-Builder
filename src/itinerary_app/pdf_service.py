from io import BytesIO
from pathlib import Path
import re

from PIL import Image as PILImage
from PIL import ImageDraw
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from itinerary_app.config import BRAND_NAME
from itinerary_app.image_loader import get_destination_image_path
from itinerary_app.models import TripRequest


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
        "brand": ParagraphStyle(
            "brand",
            parent=base_styles["BodyText"],
            fontName=fonts["subheading"],
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#c8a96a"),
            spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base_styles["Title"],
            fontName=fonts["heading"],
            fontSize=25,
            leading=31,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#10202d"),
            spaceAfter=10,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base_styles["BodyText"],
            fontName=fonts["body"],
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            parent=base_styles["Heading2"],
            fontName=fonts["subheading"],
            fontSize=16,
            leading=22,
            textColor=colors.HexColor("#10202d"),
            spaceBefore=10,
            spaceAfter=8,
        ),
        "day_title": ParagraphStyle(
            "day_title",
            parent=base_styles["Heading2"],
            fontName=fonts["heading"],
            fontSize=18,
            leading=24,
            textColor=colors.HexColor("#10202d"),
            spaceBefore=4,
            spaceAfter=10,
        ),
        "label": ParagraphStyle(
            "label",
            parent=base_styles["BodyText"],
            fontName=fonts["body_bold"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base_styles["BodyText"],
            fontName=fonts["body"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceAfter=5,
        ),
        "fine": ParagraphStyle(
            "fine",
            parent=base_styles["BodyText"],
            fontName=fonts["body"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4,
        ),
    }


def sanitize_itinerary_text(itinerary_text: str) -> str:
    cleaned_lines = []
    for line in itinerary_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = re.sub(r"[*_`#>\[\]]", "", cleaned)
        cleaned = re.sub(r"\(([^)]*)\)", lambda match: f" {match.group(1)} " if "Day" in match.group(1) else match.group(0), cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:")
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def _escape_text(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


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


def get_destination_image(destination: str):
    return get_destination_image_path(destination) or _build_cover_image()


def _page_number(canvas, doc) -> None:
    if canvas.getPageNumber() >= 2:
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawRightString(A4[0] - doc.rightMargin, 20, f"Page {canvas.getPageNumber()}")


def render_cover_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, trip_title: str) -> None:
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(_escape_text(BRAND_NAME), styles["brand"]))
    story.append(HRFlowable(width="18%", thickness=1.2, color=colors.HexColor("#c8a96a"), hAlign="CENTER"))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Image(get_destination_image(request.destination), width=6.7 * inch, height=3.75 * inch))
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(_escape_text(trip_title), styles["cover_title"]))
    story.append(Paragraph("Luxury Andaman Travel Proposal", styles["cover_subtitle"]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(_escape_text(f"Prepared for {request.customer_name}"), styles["cover_subtitle"]))
    story.append(Paragraph(_escape_text(f"Destination: {request.destination}"), styles["cover_subtitle"]))
    story.append(
        Paragraph(
            _escape_text(f"Duration: {request.number_of_days} Days / {request.number_of_nights} Nights"),
            styles["cover_subtitle"],
        )
    )
    story.append(PageBreak())


def render_day_page(story: list, styles: dict[str, ParagraphStyle], day_section: dict[str, object], include_image: bool, destination: str) -> None:
    story.append(Paragraph(_escape_text(str(day_section["heading"])), styles["day_title"]))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d6c29b")))
    story.append(Spacer(1, 0.14 * inch))
    if include_image:
        story.append(Image(get_destination_image(destination), width=6.2 * inch, height=2.65 * inch))
        story.append(Spacer(1, 0.18 * inch))
    for item in day_section["items"]:
        label = str(item["label"] or "").strip()
        content = _escape_text(str(item["content"] or "").strip())
        if label:
            story.append(Paragraph(_escape_text(f"{label}"), styles["label"]))
        story.append(Paragraph(content, styles["body"]))
    story.append(Spacer(1, 0.08 * inch))


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
        story.append(HRFlowable(width="22%", thickness=1.0, color=colors.HexColor("#c8a96a"), hAlign="LEFT"))
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
        rightMargin=52,
        leftMargin=52,
        topMargin=38,
        bottomMargin=40,
    )
    story: list = []
    render_cover_page(story, styles, request, trip_title)
    day_sections = split_itinerary_into_days(cleaned_itinerary)
    for index, section in enumerate(day_sections):
        render_day_page(
            story,
            styles,
            section,
            include_image=index == 0,
            destination=request.destination,
        )
        if index != len(day_sections) - 1:
            story.append(Spacer(1, 0.1 * inch))
    render_terms_pages(story, styles)
    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()
