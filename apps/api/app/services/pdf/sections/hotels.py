"""
PDF rendering: hotel stays page.

Uses day-wise hotel assignments from `request.daily_island_plan[].hotel`
as the definitive source. Consolidates duplicate hotel names across days
into a single card with the total night count.
"""
import logging
from collections import OrderedDict

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Spacer, Table, TableStyle

from app.schemas.trip import TripRequest
from app.services.data_loader import load_hotels
from app.services.pdf.constants import COLORS, PAGE_INNER_WIDTH
from app.services.pdf.fonts import font_map
from app.services.pdf.text_utils import escape_text

LOGGER = logging.getLogger(__name__)


def _consolidate_hotel_stays(request: TripRequest) -> list[dict]:
    """
    Read daily_island_plan[].hotel and return a deduplicated list of:
      { hotel_name, nights, first_day }
    Same hotel across any days is merged into one entry with total nights summed.
    Cards are ordered by the first day on which each hotel appears.
    """
    plans = list(request.daily_island_plan or [])
    # Ordered dict keyed by normalised hotel name to preserve insertion order
    merged: OrderedDict[str, dict] = OrderedDict()
    for plan in plans:
        name = (plan.hotel or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in merged:
            merged[key]["nights"] += 1
        else:
            merged[key] = {"hotel_name": name, "nights": 1, "first_day": plan.day_number}
    return list(merged.values())


def _lookup_hotel_metadata(hotel_name: str, all_hotels_df) -> dict:
    """
    Look up hotel metadata (location, category, description) from the hotels CSV.
    Falls back to empty strings if the hotel isn't found.
    """
    if all_hotels_df is None or all_hotels_df.empty:
        return {}
    name_lower = hotel_name.lower().strip()
    # Exact match first
    matches = all_hotels_df[all_hotels_df["hotel_name"].str.lower().str.strip() == name_lower]
    if matches.empty:
        # Fuzzy: contains
        matches = all_hotels_df[all_hotels_df["hotel_name"].str.lower().str.contains(name_lower, na=False)]
    if matches.empty:
        return {}
    row = matches.iloc[0]
    return {
        "location": str(row.get("location") or "").strip(),
        "category": str(row.get("category") or "").strip(),
        "description": str(row.get("description") or "").strip(),
    }


def _hotel_card_flowable(hotel_name: str, nights: int, meta: dict, card_width: float) -> Table:
    fonts = font_map()
    location = meta.get("location") or ""
    category = meta.get("category") or ""
    description = meta.get("description") or ""
    stay_text = f"{nights} Night" if nights == 1 else f"{nights} Nights"

    import re
    stars = ""
    match = re.search(r'(\d+)', category)
    if match:
        star_count = min(7, int(match.group(1)))
        stars = " " + ("\u2605" * star_count)

    details = [
        Paragraph(escape_text(f"{hotel_name}{stars}"), ParagraphStyle(
            "hotel_card_name", fontName=fonts["heading"], fontSize=13.5, leading=16,
            textColor=COLORS["gold"], spaceAfter=4)),
        Paragraph(escape_text(location), ParagraphStyle(
            "hotel_card_meta", fontName=fonts["body_bold"], fontSize=10.1, leading=13.5,
            textColor=COLORS["dark"], spaceAfter=3)),
        Paragraph(escape_text(category), ParagraphStyle(
            "hotel_card_meta2", fontName=fonts["body"], fontSize=9.5, leading=13,
            textColor=COLORS["soft_grey"], spaceAfter=4)),
        Paragraph(escape_text(description), ParagraphStyle(
            "hotel_card_body", fontName=fonts["body"], fontSize=9.4, leading=12.8,
            textColor=COLORS["body"], spaceAfter=4)),
        Paragraph(escape_text(f"Stay Duration: {stay_text}"), ParagraphStyle(
            "hotel_card_stay", fontName=fonts["body_bold"], fontSize=9.4, leading=12.8,
            textColor=COLORS["dark"], spaceAfter=0)),
    ]
    card = Table([[details]], colWidths=[card_width])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["card"]),
        ("BOX", (0, 0), (-1, -1), 0.8, COLORS["gold"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return card


def render_luxury_stays_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, itinerary_text: str) -> None:
    # Build consolidated stay list from day-wise assignments
    consolidated = _consolidate_hotel_stays(request)

    if not consolidated:
        LOGGER.warning("No day-wise hotel assignments found; hotel section skipped.")
        return

    # Load hotel CSV for metadata lookup
    try:
        all_hotels_df = load_hotels()
    except Exception as exc:
        LOGGER.warning("Could not load hotels CSV for metadata: %s", exc)
        all_hotels_df = None

    story.append(Paragraph("YOUR LUXURY STAYS", styles["highlights_title"]))
    story.append(Paragraph("Elegant stays selected from Darun Tourism inventory.", styles["highlights_subtitle"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.18 * inch))

    card_width = (PAGE_INNER_WIDTH - 12) / 2

    for i in range(0, len(consolidated), 2):
        left_entry = consolidated[i]
        left_meta = _lookup_hotel_metadata(left_entry["hotel_name"], all_hotels_df)
        left_card = _hotel_card_flowable(left_entry["hotel_name"], left_entry["nights"], left_meta, card_width)

        if i + 1 < len(consolidated):
            right_entry = consolidated[i + 1]
            right_meta = _lookup_hotel_metadata(right_entry["hotel_name"], all_hotels_df)
            right_card = _hotel_card_flowable(right_entry["hotel_name"], right_entry["nights"], right_meta, card_width)
        else:
            right_card = Spacer(1, 0.01 * inch)

        row_table = Table([[left_card, right_card]], colWidths=[card_width, card_width], hAlign="CENTER")
        row_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(row_table)

    story.append(PageBreak())
