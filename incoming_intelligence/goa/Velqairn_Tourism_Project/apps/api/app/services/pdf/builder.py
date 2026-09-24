"""
Top-level PDF builder: orchestrates all sections into a final PDF document.

Public API: generate_luxury_pdf(request, itinerary_text) -> bytes
"""
from io import BytesIO
from pathlib import Path

from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4

from app.schemas.trip import TripRequest
from app.services.pdf.constants import MARGINS
from app.services.pdf.fonts import build_styles
from app.services.pdf.text_utils import sanitize_itinerary_text, extract_trip_title
from app.services.pdf.sections.cover import render_cover_page, render_header, render_footer
from app.services.pdf.sections.highlights import render_highlights_page
from app.services.pdf.sections.hotels import render_luxury_stays_page
from app.services.pdf.sections.day_page import render_all_days
from app.services.pdf.sections.policies import render_terms_pages


def generate_luxury_pdf(request: TripRequest, itinerary_text: str) -> bytes:
    buffer = BytesIO()
    styles = build_styles()
    cleaned_itinerary = sanitize_itinerary_text(itinerary_text)
    trip_title = extract_trip_title(cleaned_itinerary, request.destination)
    
    import json
    try:
        json.loads(cleaned_itinerary)
    except Exception:
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
    used_images: set[Path] = set()

    render_cover_page(story, styles, request, trip_title)
    render_highlights_page(story, styles, request, cleaned_itinerary)
    render_luxury_stays_page(story, styles, request, cleaned_itinerary)
    render_all_days(story, styles, request, cleaned_itinerary, used_images)
    render_terms_pages(story, styles, request)

    document.build(
        story,
        onFirstPage=lambda canvas, doc: render_footer(canvas, doc, request),
        onLaterPages=lambda canvas, doc: (render_header(canvas, doc, request), render_footer(canvas, doc)),
    )
    return buffer.getvalue()
