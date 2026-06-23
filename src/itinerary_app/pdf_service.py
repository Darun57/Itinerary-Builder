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
MONTH_SEASONS = {
    "december": "winter",
    "january": "winter",
    "february": "winter",
    "march": "summer",
    "april": "summer",
    "may": "summer",
    "june": "monsoon",
    "july": "monsoon",
    "august": "monsoon",
    "september": "monsoon",
    "october": "shoulder",
    "november": "shoulder",
}
SEASONAL_TIPS = {
    "winter": "December to February is ideal for scuba, beach time, and sunset experiences with calmer conditions.",
    "summer": "March to May suits early-start sightseeing, beach downtime, and a relaxed midday resort pace.",
    "monsoon": "June to September may bring occasional rain showers, so flexible transfer buffers and scenic indoor moments help.",
    "shoulder": "October and November usually offer balanced weather, making them a strong window for mixed sightseeing and beach plans.",
}
DESTINATION_INSIGHT_TIPS = {
    "port blair": [
        "Port Blair works best as a heritage-led base, especially when Cellular Jail and museum visits are clustered together.",
        "Use Port Blair for a smooth arrival or departure day and keep the pace light before island transfers.",
    ],
    "swaraj dweep": [
        "Swaraj Dweep suits a premium beach rhythm, combining Radhanagar Beach, selected water activities, and resort downtime.",
        "For Swaraj Dweep, the best flow is usually one signature beach experience paired with a slower luxury afternoon.",
    ],
    "shaheed dweep": [
        "Shaheed Dweep shines with calm beach time, Natural Bridge visits, and unhurried scenic movement.",
        "Keep Shaheed Dweep soft and relaxed so guests can enjoy its quieter beaches without rushing between points.",
    ],
    "baratang": [
        "Baratang is strongest as an early-start day, especially for limestone caves, mangrove channels, and nature-focused transfers.",
        "Plan Baratang with generous road and boat buffers so the experience feels smooth rather than rushed.",
    ],
    "diglipur": [
        "Diglipur is ideal for longer north-island exploration, including Ross & Smith Islands and Saddle Peak experiences.",
        "Use Diglipur when the itinerary needs a nature-first detour with more scenic breathing room.",
    ],
}
ACTIVITY_INSIGHT_TIPS = {
    "scuba": "Scuba and snorkeling are best kept on days with calm sequencing and minimal transfer pressure.",
    "snorkel": "Snorkeling pairs well with beach time and a single major excursion rather than too many back-to-back activities.",
    "sunset cruise": "Sunset cruises work beautifully as the evening anchor after a light sightseeing day.",
    "glass bottom boat": "Glass bottom boat rides are a gentle way to add marine experience without a demanding itinerary pace.",
    "bridge": "Natural-formation visits benefit from early starts and comfortable footwear planning.",
    "trek": "Trekking days should be protected with time buffers so the guest experience stays polished and unhurried.",
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


def _split_values(text: str) -> list[str]:
    values: list[str] = []
    for chunk in re.split(r"[,\n]", str(text or "")):
        cleaned = chunk.strip()
        if not cleaned or cleaned.lower() == "none":
            continue
        values.append(cleaned)
    return values


def _clean_destination_label(text: str) -> str:
    cleaned = re.sub(r"\s*\([^)]*\)", "", str(text or "")).strip()
    return re.sub(r"\s+", " ", cleaned)


def _normalize_destination_key(text: str) -> str:
    return _clean_destination_label(text).lower()


def _extract_activity_terms(text: str) -> list[str]:
    activity_terms = []
    lower_text = str(text or "").lower()
    for keyword, label in ITINERARY_KEYWORDS.items():
        if keyword in lower_text and label not in activity_terms:
            activity_terms.append(label)
    return activity_terms


def _season_from_month(month: str) -> str:
    return MONTH_SEASONS.get(str(month or "").strip().lower(), "shoulder")


def _seasonal_advice(month: str, destination: str, activity_terms: list[str]) -> str:
    season = _season_from_month(month)
    base = SEASONAL_TIPS[season]
    destination_key = _normalize_destination_key(destination)
    destination_tip = ""
    for key, tips in DESTINATION_INSIGHT_TIPS.items():
        if key in destination_key:
            destination_tip = tips[0]
            if len(tips) > 1 and activity_terms:
                destination_tip = tips[1]
            break
    activity_tip = ""
    for term in activity_terms:
        lower_term = term.lower()
        if "scuba" in lower_term or "snorkel" in lower_term:
            activity_tip = ACTIVITY_INSIGHT_TIPS["scuba"]
            break
        if "sunset" in lower_term:
            activity_tip = ACTIVITY_INSIGHT_TIPS["sunset cruise"]
            break
        if "glass bottom" in lower_term:
            activity_tip = ACTIVITY_INSIGHT_TIPS["glass bottom boat"]
            break
        if "bridge" in lower_term:
            activity_tip = ACTIVITY_INSIGHT_TIPS["bridge"]
            break
        if "trek" in lower_term:
            activity_tip = ACTIVITY_INSIGHT_TIPS["trek"]
            break
    pieces = [base]
    if destination_tip:
        pieces.append(destination_tip)
    if activity_tip and activity_tip not in pieces:
        pieces.append(activity_tip)
    return " ".join(pieces)


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


def _extract_highlights(itinerary_text: str, request: TripRequest) -> dict[str, list[str] | str | int]:
    destinations: list[str] = []
    for value in _split_values(request.selected_destinations):
        destination_label = _clean_destination_label(value)
        if destination_label and destination_label not in destinations:
            destinations.append(destination_label)
    if not destinations:
        for raw_line in _split_values(request.daily_island_plan):
            for part in raw_line.split(":")[-1].split(","):
                destination_label = _clean_destination_label(part)
                if destination_label and destination_label not in destinations:
                    destinations.append(destination_label)
    if not destinations:
        for raw_line in itinerary_text.splitlines():
            lower_line = raw_line.lower()
            for keyword in [
                "port blair",
                "swaraj dweep",
                "shaheed dweep",
                "baratang",
                "diglipur",
                "ross island",
                "north bay",
                "jolly buoy",
                "red skin",
                "chidiya tapu",
                "wandoor",
                "long island",
                "little andaman",
            ]:
                if keyword in lower_line:
                    destination_label = _clean_destination_label(keyword.title())
                    if destination_label not in destinations:
                        destinations.append(destination_label)
    if not destinations:
        destinations = [_clean_destination_label(request.destination or "Andaman Islands")]

    activities = [value for value in _split_values(request.preferred_activities)]
    if not activities:
        activities = _extract_activity_terms(itinerary_text)
    if not activities:
        activities = ["Curated sightseeing", "Luxury pacing", "Scenic transfers"]

    travel_style = _split_values(request.travel_style)
    hotel_category = request.hotel_category_preference or "Luxury"

    return {
        "destinations": destinations[:6],
        "activities": activities[:6],
        "travel_style": travel_style[:3] or ["Luxury"],
        "number_of_days": request.number_of_days,
        "number_of_nights": request.number_of_nights,
        "hotel_category": hotel_category,
    }


def render_destination_insight_box(
    story: list,
    styles: dict[str, ParagraphStyle],
    request: TripRequest,
    destination: str,
    day_number: int,
    day_section: dict[str, object],
) -> None:
    day_titles = ["INSIDER TIP", "DID YOU KNOW?", "LOCAL RECOMMENDATION", "TRAVEL ADVICE"]
    selected_title = day_titles[(max(day_number, 1) - 1) % len(day_titles)]
    activity_terms = _extract_activity_terms(" ".join(str(item.get("content") or "") for item in day_section.get("items", [])))
    if not activity_terms:
        activity_terms = _split_values(request.preferred_activities)
    advice = _seasonal_advice(request.travel_month, destination, activity_terms)

    box = Table(
        [
            [
                Paragraph(_escape_text(selected_title), styles["section_title"]),
                Paragraph(_escape_text(advice), styles["fine"]),
            ]
        ],
        colWidths=[1.7 * inch, PAGE_INNER_WIDTH - 1.7 * inch - 10],
    )
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLORS["soft_white"]),
                ("BOX", (0, 0), (-1, -1), 0.8, COLORS["gold"]),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, COLORS["line"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(KeepTogether([Spacer(1, 0.08 * inch), box, Spacer(1, 0.08 * inch)]))


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
    story.append(Paragraph("Destinations Covered", styles["section_title"]))
    for item in highlights["destinations"]:
        story.append(Paragraph(f"\u2022 {_escape_text(item)}", styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Top Activities", styles["section_title"]))
    for item in highlights["activities"]:
        story.append(Paragraph(f"\u2022 {_escape_text(item)}", styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Travel Style", styles["section_title"]))
    story.append(Paragraph(_escape_text(", ".join(highlights["travel_style"])), styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Number of Days", styles["section_title"]))
    story.append(Paragraph(_escape_text(f"{highlights['number_of_days']} Days | {highlights['number_of_nights']} Nights"), styles["highlight_body"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Hotel Category", styles["section_title"]))
    story.append(Paragraph(_escape_text(str(highlights["hotel_category"])), styles["highlight_body"]))
    story.append(PageBreak())

def _count_location_days(text: str, location: str) -> int:
    location_key = _normalize_destination_key(location)
    if not location_key:
        return 0

    count = 0
    for line in _split_values(text):
        if location_key in _normalize_destination_key(line):
            count += 1
    return count


def _count_location_days_in_itinerary(itinerary_text: str, location: str) -> int:
    location_key = _normalize_destination_key(location)
    if not location_key:
        return 0

    count = 0
    for day_section in split_itinerary_into_days(itinerary_text):
        day_text = " ".join(
            [str(day_section.get("heading") or ""), " ".join(str(item.get("content") or "") for item in day_section.get("items", []))]
        ).lower()
        if location_key in day_text:
            count += 1
    return count


def _hotel_stay_text(hotel_row: dict[str, object], request: TripRequest, itinerary_text: str) -> str:
    location = str(hotel_row.get("location") or "").strip()
    stay_days = _count_location_days(request.daily_island_plan, location)
    if stay_days == 0 and itinerary_text:
        stay_days = _count_location_days_in_itinerary(itinerary_text, location)
    if stay_days > 0:
        return f"{stay_days} Night" if stay_days == 1 else f"{stay_days} Nights"
    return "As Per Itinerary"


def _hotel_card_flowable(hotel_row: dict[str, object], request: TripRequest, itinerary_text: str, card_width: float) -> Table:
    hotel_name = str(hotel_row.get("hotel_name") or "").strip()
    location = str(hotel_row.get("location") or "").strip()
    category = str(hotel_row.get("category") or "").strip()
    description = str(hotel_row.get("description") or "").strip()
    stay_text = _hotel_stay_text(hotel_row, request, itinerary_text)
    image_path = get_hotel_image_path(hotel_name)
    if image_path:
        image_flowable = Image(str(image_path), width=card_width - 14, height=1.45 * inch)
    else:
        image_flowable = Spacer(1, 1.45 * inch)
    details = [
        Paragraph(
            _escape_text(f"{hotel_name} \u2605\u2605\u2605\u2605\u2605"),
            ParagraphStyle("hotel_card_name", fontName=_font_map()["heading"], fontSize=13.5, leading=16, textColor=COLORS["gold"], spaceAfter=4),
        ),
        Paragraph(
            _escape_text(location),
            ParagraphStyle("hotel_card_meta", fontName=_font_map()["body_bold"], fontSize=10.1, leading=13.5, textColor=COLORS["dark"], spaceAfter=3),
        ),
        Paragraph(
            _escape_text(category),
            ParagraphStyle("hotel_card_meta2", fontName=_font_map()["body"], fontSize=9.5, leading=13, textColor=COLORS["soft_grey"], spaceAfter=4),
        ),
        Paragraph(
            _escape_text(description),
            ParagraphStyle("hotel_card_body", fontName=_font_map()["body"], fontSize=9.4, leading=12.8, textColor=COLORS["body"], spaceAfter=4),
        ),
        Paragraph(
            _escape_text(f"Stay Duration: {stay_text}"),
            ParagraphStyle("hotel_card_stay", fontName=_font_map()["body_bold"], fontSize=9.4, leading=12.8, textColor=COLORS["dark"], spaceAfter=0),
        ),
    ]
    card = Table([[image_flowable], [details]], colWidths=[card_width])
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


def render_luxury_stays_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, itinerary_text: str) -> None:
    hotel_frame = recommend_hotels(request)
    if hotel_frame.empty:
        return
    story.append(Paragraph("YOUR LUXURY STAYS", styles["highlights_title"]))
    story.append(Paragraph("Elegant stays selected from Darun Tourism inventory.", styles["highlights_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.18 * inch))

    card_width = (PAGE_INNER_WIDTH - 12) / 2
    hotel_rows = [row.to_dict() for _, row in hotel_frame.iterrows()]
    for index in range(0, len(hotel_rows), 2):
        left_card = _hotel_card_flowable(hotel_rows[index], request, itinerary_text, card_width)
        right_card = (
            _hotel_card_flowable(hotel_rows[index + 1], request, itinerary_text, card_width)
            if index + 1 < len(hotel_rows)
            else Spacer(1, 0.01 * inch)
        )
        row_table = Table([[left_card, right_card]], colWidths=[card_width, card_width], hAlign="CENTER")
        row_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(row_table)
    story.append(PageBreak())


def render_day_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, day_section: dict[str, object], destination: str, day_number: int) -> None:
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
    render_destination_insight_box(story, styles, request, destination, day_number, day_section)
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
    render_luxury_stays_page(story, styles, request, cleaned_itinerary)
    day_sections = split_itinerary_into_days(cleaned_itinerary)
    for index, section in enumerate(day_sections):
        render_day_page(story, styles, request, section, destination=request.destination, day_number=index + 1)
        if index != len(day_sections) - 1:
            story.append(PageBreak())
    render_terms_pages(story, styles)
    document.build(
        story,
        onFirstPage=lambda canvas, doc: render_footer(canvas, doc),
        onLaterPages=lambda canvas, doc: (render_header(canvas, doc, request), render_footer(canvas, doc)),
    )
    return buffer.getvalue()
