"""
PDF rendering: day-by-day itinerary pages.
"""
import logging
import re
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import CondPageBreak, HRFlowable, Image, PageBreak, Paragraph, Spacer, Table, TableStyle

from app.schemas.trip import TripRequest
from app.services.pdf.constants import COLORS, PAGE_INNER_WIDTH, SECTION_LABELS
from app.services.pdf.day_parser import build_day_context, generate_day_subtitle, split_itinerary_into_days
from app.services.pdf.image_resolver import resolve_day_image
from app.services.pdf.text_utils import (
    clean_destination_label,
    escape_text,
    unique_values,
    word_count,
)

LOGGER = logging.getLogger(__name__)


def _get_date_for_day(date_str: str, day_index: int) -> str:
    """Calculate the date for a specific day index (0-based) given a start date string."""
    if not date_str:
        return ""
    from datetime import datetime, timedelta
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            target_dt = dt + timedelta(days=day_index)
            return target_dt.strftime("%d %b %Y")
        except ValueError:
            continue
    return ""


def _normalize_day_items(day_section: dict[str, object], day_context: dict[str, object], request: TripRequest, is_final_day: bool) -> list[dict[str, object]]:
    incoming_items = list(day_section.get("items") or [])
    result = []
    for item in incoming_items:
        label = str(item.get("label") or "").strip()
        is_bullets = bool(item.get("is_bullets"))
        bullets = item.get("bullets")
        is_intro = bool(item.get("is_intro"))

        if is_bullets and bullets:
            clean_bullets = [str(b).strip() for b in bullets if str(b).strip()]
            if clean_bullets:
                result.append({
                    "label": label,
                    "bullets": clean_bullets,
                    "is_bullets": True,
                })
            continue

        paragraphs = item.get("paragraphs")
        if paragraphs:
            clean_paragraphs = [str(p).strip() for p in paragraphs if str(p).strip()]
            if clean_paragraphs:
                result.append({
                    "label": label,
                    "paragraphs": clean_paragraphs,
                    "content": "\n\n".join(clean_paragraphs),
                    "is_intro": is_intro,
                })
        else:
            content = str(item.get("content") or "").strip()
            if content:
                paras = [p.strip() for p in content.split("\n\n") if p.strip()]
                result.append({
                    "label": label,
                    "paragraphs": paras,
                    "content": content,
                    "is_intro": is_intro,
                })
    return result


def _estimate_day_block_height(items: list[dict[str, object]], has_image: bool) -> float:
    height = 0.55 * inch
    height += 2.75 * inch if has_image else 0.55 * inch
    for item in items:
        if item.get("is_bullets") and item.get("bullets"):
            content_words = sum(max(word_count(str(b) or ""), 1) for b in item["bullets"])
        else:
            paragraphs = item.get("paragraphs") or [item.get("content")]
            content_words = sum(max(word_count(str(p) or ""), 1) for p in paragraphs if p)
        label_words = max(word_count(str(item.get("label") or "")), 1)
        height += 0.24 * inch
        height += 0.16 * inch if item.get("label") else 0
        height += max(0.75 * inch, ((content_words + label_words) / 14.0) * 0.28 * inch)
        height += 0.16 * inch
        height += 0.08 * inch
    height += 0.25 * inch
    return height


def _fallback_day_section(day_number: int, request: TripRequest) -> dict[str, object]:
    base_destination = clean_destination_label(request.destination or "Andaman Islands")
    is_departure = (day_number == request.number_of_days)
    is_simple = (getattr(request, "day_wise_style", "luxury_narrative") in ["simple_itinerary", "simple"])

    if is_departure:
        heading = f"DAY {day_number} | (Departure)"
        if is_simple:
            bullets = [
                "Breakfast at hotel",
                "Hotel check-out and luggage assistance",
                f"Private transfer to Veer Savarkar International Airport, Port Blair",
                "Board scheduled return flight with memorable experiences",
            ]
            return {
                "heading": heading,
                "is_departure_day": True,
                "custom_title": "Departure",
                "items": [
                    {
                        "label": "",
                        "paragraphs": ["Morning check-out followed by assisted airport transfer for your return flight home."],
                        "is_intro": True,
                    },
                    {
                        "label": "END OF THE JOURNEY",
                        "bullets": bullets,
                        "is_bullets": True,
                    },
                    {
                        "label": "TRANSPORT & LOGISTICS",
                        "paragraphs": ["Private transfer from hotel to airport."],
                        "content": "Private transfer from hotel to airport.",
                    },
                ],
            }

        return {
            "heading": heading,
            "is_departure_day": True,
            "custom_title": "Departure",
            "items": [
                {
                    "label": "END OF THE JOURNEY",
                    "paragraphs": [
                        f"After a relaxed morning at the hotel, the journey concludes with a comfortable transfer from the hotel to the airport. Our team will assist {request.customer_name or 'the guests'} and their family with their departure, ensuring a smooth and hassle-free journey as they head back home with wonderful memories of their island holiday.",
                        f"As the journey comes to an end, we sincerely thank {request.customer_name or 'the guests'} and their family for choosing Darun Tourism to be a part of their memorable island getaway. It has been our pleasure to create beautiful experiences and cherished moments for your family throughout the journey. We wish you a safe and comfortable departure, and hope to welcome you again soon for another unforgettable adventure.",
                    ],
                }
            ],
        }

    heading = f"DAY {day_number} | ({base_destination})"
    if is_simple:
        bullets = [
            "After breakfast, pickup from hotel",
            f"Proceed for sightseeing across {base_destination}",
            "Return transfer to hotel",
            f"Overnight stay at {base_destination}",
        ]
        return {
            "heading": heading,
            "is_departure_day": False,
            "custom_title": f"{base_destination} Tour",
            "items": [
                {
                    "label": "",
                    "paragraphs": [f"Explore {base_destination} with curated local sightseeing."],
                    "is_intro": True,
                },
                {
                    "label": "TODAY'S SCHEDULE",
                    "bullets": bullets,
                    "is_bullets": True,
                },
                {
                    "label": "TRANSPORT & LOGISTICS",
                    "paragraphs": ["Private vehicle transfers for all scheduled sightseeing."],
                    "content": "Private vehicle transfers for all scheduled sightseeing.",
                },
                {
                    "label": "HOTEL & OVERNIGHT",
                    "paragraphs": [f"Overnight stay at {base_destination}."],
                    "content": f"Overnight stay at {base_destination}.",
                },
            ],
        }

    return {
        "heading": heading,
        "is_departure_day": False,
        "custom_title": f"Discovering {base_destination}",
        "items": [
            {
                "label": "Visiting Places And Destination Story",
                "paragraphs": [
                    f"The day begins with curated exploration of the iconic highlights of {base_destination}, tailored for relaxation and island discovery.",
                    f"Surrounded by the azure waters of the Bay of Bengal, {base_destination} offers a serene harmony of tropical scenery, coastal history, and island charm.",
                ],
            },
            {
                "label": "Today's Journey",
                "paragraphs": [
                    "For the places highlighted above, private vehicle transfers ensure a smooth and relaxing day of sightseeing across the island."
                ],
            },
            {
                "label": "Hotel Experience",
                "paragraphs": [
                    "A comfortable stay offering relaxing surroundings and warm hospitality—perfect for unwinding after the day's adventures."
                ],
            },
        ],
    }


def render_day_page(
    story: list,
    styles: dict[str, ParagraphStyle],
    request: TripRequest,
    day_section: dict[str, object],
    destination: str,
    day_number: int,
    used_images: set[Path],
    is_final_day: bool = False,
) -> None:
    day_context = build_day_context(day_section, request, day_number, used_images)
    subtitle = generate_day_subtitle(day_context)
    heading = str(day_section["heading"])
    clean_heading = re.sub(r"^day\s*", "DAY ", heading, flags=re.IGNORECASE)
    day_date = _get_date_for_day(request.arrival_date, day_number - 1)
    if day_date:
        clean_heading = f"{clean_heading} | {day_date}"
    image_path = resolve_day_image(request, day_number, used_images, is_final_day=is_final_day)
    items = _normalize_day_items(day_section, day_context, request, is_final_day)

    day_flowables: list = [
        Spacer(1, 0.04 * inch),
        Paragraph(escape_text(clean_heading), styles["day_title"]),
        HRFlowable(width="100%", thickness=0.7, color=COLORS["line"]),
        Spacer(1, 0.1 * inch),
        Paragraph(escape_text(subtitle), styles["section_title"]),
        Spacer(1, 0.04 * inch),
    ]
    if image_path:
        img_height = 2.60 * inch
        img = Image(str(image_path), width=PAGE_INNER_WIDTH, height=img_height)
        img_table = Table([[img]], colWidths=[PAGE_INNER_WIDTH], rowHeights=[img_height])
        img_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 0.6, COLORS["line"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        day_flowables.append(img_table)
        day_flowables.append(Spacer(1, 0.12 * inch))
    else:
        day_flowables.append(Spacer(1, 0.05 * inch))

    for item in items:
        label = str(item.get("label") or "").strip()
        is_bullets = bool(item.get("is_bullets"))
        bullets = item.get("bullets")
        paragraphs = item.get("paragraphs") or [item.get("content")]

        if label:
            day_flowables.append(Paragraph(escape_text(label), styles["label"]))
            day_flowables.append(Spacer(1, 0.04 * inch))

        if is_bullets and bullets:
            for b in bullets:
                b_str = str(b).strip()
                if not b_str:
                    continue
                if b_str.startswith("→") or b_str.startswith("->") or "→" in b_str[:4]:
                    clean_b = b_str.lstrip(" -→>").strip()
                    b_style = styles.get("bullet_subitem", styles["body"])
                    day_flowables.append(Paragraph(f"&nbsp;&nbsp;&rarr;&nbsp;&nbsp;{escape_text(clean_b)}", b_style))
                else:
                    clean_b = b_str.lstrip(" •-*").strip()
                    b_style = styles.get("bullet_item", styles["body"])
                    day_flowables.append(Paragraph(f"&bull;&nbsp;&nbsp;{escape_text(clean_b)}", b_style))
        else:
            for p_idx, para in enumerate(paragraphs):
                para_str = escape_text(str(para or "").strip())
                if not para_str:
                    continue
                if p_idx > 0:
                    day_flowables.append(Spacer(1, 0.06 * inch))
                if item.get("is_intro"):
                    day_flowables.append(Paragraph(para_str, styles.get("bullet_lead", styles["body"])))
                else:
                    day_flowables.append(Paragraph(para_str, styles["body"]))

        day_flowables.append(Spacer(1, 0.04 * inch))
        day_flowables.append(HRFlowable(width="100%", thickness=0.25, color=COLORS["line"]))
        day_flowables.append(Spacer(1, 0.04 * inch))

    day_flowables.append(Spacer(1, 0.06 * inch))
    day_flowables.append(HRFlowable(width="100%", thickness=0.4, color=COLORS["soft_grey"]))
    day_flowables.append(Spacer(1, 0.02 * inch))
    story.extend(day_flowables)


def render_all_days(
    story: list,
    styles: dict[str, ParagraphStyle],
    request: TripRequest,
    cleaned_itinerary: str,
    used_images: set[Path],
) -> None:
    day_sections = split_itinerary_into_days(cleaned_itinerary)
    total_trip_days = max(int(request.number_of_days or 0), len(day_sections))
    if len(day_sections) < total_trip_days:
        LOGGER.warning("Itinerary only produced %s day sections; expected %s. Filling missing days.", len(day_sections), total_trip_days)
        for day_number in range(len(day_sections) + 1, total_trip_days + 1):
            day_sections.append(_fallback_day_section(day_number, request))



    for index, section in enumerate(day_sections[:total_trip_days]):
        if index > 0:
            story.append(PageBreak())
        render_day_page(
            story, styles, request, section,
            destination=request.destination,
            day_number=index + 1,
            used_images=used_images,
            is_final_day=(index + 1 == total_trip_days),
        )

    assert len(day_sections[:total_trip_days]) == total_trip_days
