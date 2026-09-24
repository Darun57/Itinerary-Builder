"""
PDF rendering: cover page and page header/footer.
"""
import logging
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Image, PageBreak, Paragraph, Spacer

from app.core.config import BRAND_NAME
from app.schemas.trip import TripRequest
from app.services.destination_registry import get_destination_context
from app.services.image_loader import get_cover_image_path, get_fallback_image_path
from app.services.pdf.constants import COLORS, PAGE_WIDTH, PAGE_HEIGHT
from app.services.pdf.image_resolver import build_cover_image
from app.services.pdf.text_utils import escape_text

LOGGER = logging.getLogger(__name__)


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


def render_footer(canvas, doc, request: TripRequest = None) -> None:
    canvas.saveState()
    ctx = get_destination_context(request.destination if request else None)

    if canvas.getPageNumber() == 1:
        # ── Cover image ──────────────────────────────────────────────────────
        # For non-Andaman: try destination-namespaced image first
        cover_image = None
        if not ctx.is_andaman:
            from app.services.destination_registry import DESTINATION_ROOT
            dest_slug = ctx.destination_id
            dest_img_dir = DESTINATION_ROOT / dest_slug / "images"
            for ext in ("jpg", "jpeg", "png", "webp"):
                candidate = dest_img_dir / f"cover.{ext}"
                if candidate.exists():
                    cover_image = candidate
                    break
        if cover_image is None and ctx.is_andaman:
            cover_image = get_cover_image_path() or get_fallback_image_path()

        img_height = 325
        img_y = PAGE_HEIGHT - img_height
        try:
            from reportlab.lib.utils import ImageReader
            if cover_image:
                img = ImageReader(str(cover_image))
            else:
                img = ImageReader(build_cover_image())
            canvas.drawImage(img, 0, img_y, width=PAGE_WIDTH, height=img_height, preserveAspectRatio=False)
        except Exception as e:
            LOGGER.error(f"Error drawing cover image: {e}")

        # ── Brand text overlay (top-left) — destination-aware ─────────────────
        canvas.setFont("Helvetica-Bold", 10)
        canvas.setFillColor(COLORS["gold"])
        if ctx.is_andaman:
            canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 28, "ANDAMAN DARUN")
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(COLORS["white"])
            canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 40, "TOURS & TRAVELS")
        else:
            canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 28, "DARUN TOURISM")
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(COLORS["white"])
            canvas.drawString(doc.leftMargin, PAGE_HEIGHT - 40, "LUXURY TRAVEL")

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(COLORS["white"])
        canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, PAGE_HEIGHT - 32, "Page 1")

        # ── Bottom brand bar — destination-aware ──────────────────────────────
        canvas.setStrokeColor(COLORS["line"])
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 34, PAGE_WIDTH - doc.rightMargin, 34)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.setFillColor(COLORS["dark"])
        if ctx.is_andaman:
            canvas.drawString(doc.leftMargin, 18, "Darun Tourism | Andaman Specialist")
        else:
            canvas.drawString(doc.leftMargin, 18, f"Darun Tourism | {ctx.display_name} Specialist")
        canvas.setFont("Helvetica", 8.5)
        canvas.drawString(doc.leftMargin + 155, 18, "|   Luxury Travel Specialists")
        canvas.setFillColor(COLORS["gold"])
        canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 18, "Page 1")
    else:
        canvas.setStrokeColor(COLORS["line"])
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 34, PAGE_WIDTH - doc.rightMargin, 34)
        canvas.setFont("Helvetica", 8.7)
        canvas.setFillColor(COLORS["soft_grey"])
        canvas.drawString(doc.leftMargin, 20, "Darun Tourism | Luxury Travel Specialists")
        canvas.drawRightString(PAGE_WIDTH - doc.rightMargin, 20, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def render_cover_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest, trip_title: str) -> None:
    # Top bar is 65, Image is 260. Total 325. We need to push content down.
    # The default top margin is 40. We need to push by 325 - 40 = 285 points.
    story.append(Spacer(1, 285))
    story.append(Spacer(1, 0.4 * inch))
    
    # Title — uses destination name and the same heading font as day/highlights pages
    style_title = ParagraphStyle(
        "cover_main_title",
        parent=styles["cover_title"],
        fontSize=24,
        leading=30,
        textColor=COLORS["navy"],
        fontName=styles["day_title"].fontName,
        alignment=1,
        spaceAfter=8,
    )
    story.append(Paragraph(escape_text(request.destination), style_title))

    # Subtitle — destination-aware proposal label
    style_sub = ParagraphStyle(
        "cover_sub_title",
        parent=styles["cover_subtitle"],
        fontSize=10,
        leading=14,
        textColor=COLORS["soft_grey"],
        fontName="Helvetica-Bold",
        alignment=1,
        spaceAfter=15,
    )
    from reportlab.lib import colors
    teal_color = colors.HexColor("#3b82f6")
    style_sub.textColor = teal_color
    _ctx = get_destination_context(request.destination)
    proposal_subtitle = f"LUXURY {_ctx.display_name.upper()} TRAVEL PROPOSAL"
    story.append(Paragraph(proposal_subtitle, style_sub))
    
    # Gold line
    story.append(HRFlowable(width="10%", thickness=1.5, color=COLORS["gold"], hAlign="CENTER", spaceAfter=40))
    story.append(Spacer(1, 0.4 * inch))
    
    # Details Grid
    style_label = ParagraphStyle(
        "cover_grid_label",
        parent=styles["fine"],
        fontSize=8,
        leading=10,
        textColor=teal_color,
        fontName="Helvetica-Bold",
        alignment=1,
        spaceAfter=4,
    )
    style_val = ParagraphStyle(
        "cover_grid_val",
        parent=styles["body"],
        fontSize=11,
        leading=14,
        textColor=COLORS["dark"],
        fontName="Helvetica",
        alignment=1,
    )
    
    col1 = [
        Paragraph("PREPARED FOR", style_label),
        Paragraph(escape_text(request.customer_name), style_val),
        Spacer(1, 0.25 * inch),
        Paragraph("DURATION", style_label),
        Paragraph(escape_text(f"{request.number_of_days} Days / {request.number_of_nights} Nights"), style_val),
    ]
    
    col2 = [
        Paragraph("DESTINATION", style_label),
        Paragraph(escape_text(request.destination), style_val),
        Spacer(1, 0.25 * inch),
        Paragraph("PACKAGE TYPE", style_label),
        Paragraph("Premium Luxury", style_val),
    ]
    
    from reportlab.platypus import Table, TableStyle
    grid = Table([[col1, col2]], colWidths=[PAGE_WIDTH/2 - 52, PAGE_WIDTH/2 - 52])
    grid.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(grid)
    story.append(PageBreak())
