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
    If the final day is marked as 'Departure', it is not treated as an overnight stay.
    """
    plans = list(request.daily_island_plan or [])
    total_days = int(request.number_of_days or len(plans))
    # Ordered dict keyed by normalised hotel name to preserve insertion order
    merged: OrderedDict[str, dict] = OrderedDict()
    for plan in plans:
        is_final = (plan.day_number == total_days)
        is_dep = is_final and (
            getattr(plan, "is_departure_day", False)
            or (plan.primary_island or "").strip().lower() == "departure"
            or any(str(a).strip().lower() == "departure" for a in (plan.attractions or []))
        )
        if is_dep:
            continue

        name = (plan.hotel or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in merged:
            merged[key]["nights"] += 1
        else:
            merged[key] = {"hotel_name": name, "nights": 1, "first_day": plan.day_number}
    return list(merged.values())


from reportlab.lib import colors

def _lookup_hotel_metadata(hotel_name: str, all_hotels_df) -> dict:
    """
    Look up hotel metadata (location, category, description) from the hotels CSV.
    Uses multi-strategy fuzzy matching and provides authentic Andaman fallbacks
    so no hotel card ever has missing fields.
    """
    meta = {"location": "", "category": "", "room_type": "", "description": ""}
    name_clean = hotel_name.strip()
    name_lower = name_clean.lower()

    if all_hotels_df is not None and not all_hotels_df.empty:
        # 1. Exact match
        matches = all_hotels_df[all_hotels_df["hotel_name"].str.lower().str.strip() == name_lower]
        # 2. Substring match (CSV name in input or input in CSV name)
        if matches.empty:
            matches = all_hotels_df[all_hotels_df["hotel_name"].apply(
                lambda x: str(x).lower().strip() in name_lower or name_lower in str(x).lower().strip()
            )]
        # 3. Token match
        if matches.empty:
            tokens = [t for t in name_lower.split() if len(t) > 3 and t not in ["hotel", "resort", "spa", "beach", "view", "island"]]
            if tokens:
                matches = all_hotels_df[all_hotels_df["hotel_name"].apply(
                    lambda x: any(t in str(x).lower() for t in tokens)
                )]
        if not matches.empty:
            row = matches.iloc[0]
            meta["location"] = str(row.get("location") or "").strip()
            meta["category"] = str(row.get("category") or "").strip()
            meta["room_type"] = str(row.get("room_type") or "").strip()
            meta["description"] = str(row.get("description") or "").strip()

    # Smart fallbacks so no card ever has missing fields:
    if not meta["location"]:
        if any(k in name_lower for k in ["neil", "shaheed", "samssara", "tango"]):
            meta["location"] = "Shaheed Dweep (Neil)"
        elif any(k in name_lower for k in ["havelock", "swaraj", "barefoot", "exotica", "symphony palms", "silver sand"]):
            meta["location"] = "Swaraj Dweep (Havelock)"
        elif any(k in name_lower for k in ["baratang", "limestone"]):
            meta["location"] = "Baratang Island"
        else:
            meta["location"] = "Port Blair"
    elif "(" not in meta["location"]:
        loc_l = meta["location"].lower()
        if "shaheed" in loc_l or "neil" in loc_l:
            meta["location"] = "Shaheed Dweep (Neil)"
        elif "swaraj" in loc_l or "havelock" in loc_l:
            meta["location"] = "Swaraj Dweep (Havelock)"

    if not meta["category"]:
        meta["category"] = "5 Star Luxury" if any(k in name_lower for k in ["taj", "seashell", "welcomhotel", "sinclairs", "samssara"]) else "4 Star Premium"

    if not meta["description"]:
        meta["description"] = f"Curated luxury retreat in {meta['location']} offering premium comforts, sea-breeze relaxation, and attentive hospitality."

    return meta


def _build_hotel_card_flowables(hotel_name: str, nights: int, meta: dict) -> list:
    fonts = font_map()
    location = meta.get("location") or ""
    category = meta.get("category") or ""
    room_type = meta.get("room_type") or ""
    description = meta.get("description") or ""
    stay_text = f"{nights} Night" if nights == 1 else f"{nights} Nights"

    import re
    stars = ""
    match = re.search(r'(\d+)', category)
    if match:
        star_count = min(7, int(match.group(1)))
        stars = " " + ("\u2605" * star_count)
    elif "luxury" in category.lower():
        stars = " \u2605\u2605\u2605\u2605\u2605"

    sub_parts = []
    if category:
        sub_parts.append(category)
    if room_type:
        sub_parts.append(f"Room: {room_type}")
    sub_line = " \u2022 ".join(sub_parts) if sub_parts else category

    flowables = [
        Paragraph(escape_text(f"{hotel_name}{stars}"), ParagraphStyle(
            "hotel_card_name", fontName=fonts["heading"], fontSize=13.0, leading=16.0,
            textColor=COLORS["gold"], spaceAfter=4)),
        Paragraph(escape_text(location), ParagraphStyle(
            "hotel_card_meta", fontName=fonts["body_bold"], fontSize=10.0, leading=13.5,
            textColor=COLORS["dark"], spaceAfter=3)),
        Paragraph(escape_text(sub_line), ParagraphStyle(
            "hotel_card_meta2", fontName=fonts["body"], fontSize=9.5, leading=13.0,
            textColor=COLORS["soft_grey"], spaceAfter=4)),
        Paragraph(escape_text(description), ParagraphStyle(
            "hotel_card_body", fontName=fonts["body"], fontSize=9.3, leading=13.0,
            textColor=COLORS["body"], spaceAfter=6)),
        Paragraph(escape_text(f"Stay Duration: {stay_text}"), ParagraphStyle(
            "hotel_card_stay", fontName=fonts["body_bold"], fontSize=9.4, leading=13.0,
            textColor=COLORS["dark"], spaceAfter=0)),
    ]
    return flowables


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

    gutter = 14
    card_width = (PAGE_INNER_WIDTH - gutter) / 2
    content_w = card_width - 24  # 12pt left + 12pt right padding

    card_flowables_list = []
    measured_heights = []
    for entry in consolidated:
        meta = _lookup_hotel_metadata(entry["hotel_name"], all_hotels_df)
        if not meta.get("room_type") and getattr(request, "room_type_preference", None):
            meta["room_type"] = request.room_type_preference
        flowables = _build_hotel_card_flowables(entry["hotel_name"], entry["nights"], meta)
        card_flowables_list.append(flowables)

        # Measure required height
        h = 24  # 12pt top + 12pt bottom padding
        for f in flowables:
            _, fh = f.wrap(content_w, 1000)
            h += fh + (getattr(f.style, "spaceAfter", 0) if hasattr(f, "style") else 0)
        measured_heights.append(h)

    uniform_card_h = max(measured_heights) + 10 if measured_heights else 1.8 * inch
    uniform_card_h = max(uniform_card_h, 1.75 * inch)

    for i in range(0, len(card_flowables_list), 2):
        left_flowables = card_flowables_list[i]
        has_right = (i + 1 < len(card_flowables_list))
        right_flowables = card_flowables_list[i + 1] if has_right else ""

        row_table = Table(
            [[left_flowables, "", right_flowables]],
            colWidths=[card_width, gutter, card_width],
            rowHeights=[uniform_card_h],
            hAlign="CENTER"
        )
        t_style = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            # Left Card
            ("BACKGROUND", (0, 0), (0, 0), COLORS["card"]),
            ("BOX", (0, 0), (0, 0), 0.75, COLORS["gold"]),
            ("LEFTPADDING", (0, 0), (0, 0), 12),
            ("RIGHTPADDING", (0, 0), (0, 0), 12),
            ("TOPPADDING", (0, 0), (0, 0), 12),
            ("BOTTOMPADDING", (0, 0), (0, 0), 12),
            # Gutter
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (1, 0), (1, 0), 0),
            ("BOTTOMPADDING", (1, 0), (1, 0), 0),
        ]
        if has_right:
            t_style.extend([
                # Right Card
                ("BACKGROUND", (2, 0), (2, 0), COLORS["card"]),
                ("BOX", (2, 0), (2, 0), 0.75, COLORS["gold"]),
                ("LEFTPADDING", (2, 0), (2, 0), 12),
                ("RIGHTPADDING", (2, 0), (2, 0), 12),
                ("TOPPADDING", (2, 0), (2, 0), 12),
                ("BOTTOMPADDING", (2, 0), (2, 0), 12),
            ])
        else:
            t_style.extend([
                ("BACKGROUND", (2, 0), (2, 0), colors.transparent),
                ("LEFTPADDING", (2, 0), (2, 0), 0),
                ("RIGHTPADDING", (2, 0), (2, 0), 0),
                ("TOPPADDING", (2, 0), (2, 0), 0),
                ("BOTTOMPADDING", (2, 0), (2, 0), 0),
            ])
        row_table.setStyle(TableStyle(t_style))
        story.append(row_table)
        story.append(Spacer(1, 0.16 * inch))

    story.append(PageBreak())

