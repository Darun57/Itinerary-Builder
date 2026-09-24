"""
Font loading and paragraph style construction.
"""
from pathlib import Path

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.services.pdf.constants import COLORS, FONT_DIRS, FONT_CANDIDATES


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


def font_map() -> dict[str, str]:
    """Return a mapping of role → registered font name."""
    return {
        "heading": _load_font("heading", FONT_CANDIDATES["heading"]),
        "subheading": _load_font("subheading", FONT_CANDIDATES["subheading"]),
        "body": _load_font("body", FONT_CANDIDATES["body"]),
        "body_bold": _load_font("body_bold", FONT_CANDIDATES["body_bold"]),
    }


def build_styles() -> dict[str, ParagraphStyle]:
    fonts = font_map()
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle("brand", parent=base["BodyText"], fontName=fonts["subheading"], fontSize=11, leading=14, alignment=TA_CENTER, textColor=COLORS["gold"], spaceAfter=8),
        "cover_title": ParagraphStyle("cover_title", parent=base["Title"], fontName=fonts["heading"], fontSize=27, leading=33, alignment=TA_CENTER, textColor=COLORS["dark"], spaceAfter=10),
        "cover_subtitle": ParagraphStyle("cover_subtitle", parent=base["BodyText"], fontName=fonts["body"], fontSize=11, leading=16, alignment=TA_CENTER, textColor=COLORS["soft_grey"], spaceAfter=4),
        "section_title": ParagraphStyle("section_title", parent=base["Heading2"], fontName=fonts["subheading"], fontSize=15, leading=21, textColor=COLORS["dark"], spaceBefore=10, spaceAfter=8),
        "day_title": ParagraphStyle("day_title", parent=base["Heading2"], fontName=fonts["heading"], fontSize=18, leading=24, textColor=COLORS["dark"], spaceBefore=4, spaceAfter=8),
        "label": ParagraphStyle("label", parent=base["BodyText"], fontName=fonts["body_bold"], fontSize=10.5, leading=15, textColor=COLORS["dark"], spaceAfter=3),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=fonts["body"], fontSize=10.5, leading=15, textColor=COLORS["body"], spaceAfter=5),
        "fine": ParagraphStyle("fine", parent=base["BodyText"], fontName=fonts["body"], fontSize=9.5, leading=14, textColor=COLORS["soft_grey"], spaceAfter=4),
        "highlights_title": ParagraphStyle("highlights_title", parent=base["Heading2"], fontName=fonts["heading"], fontSize=21, leading=26, alignment=TA_CENTER, textColor=COLORS["dark"], spaceAfter=10),
        "highlights_subtitle": ParagraphStyle("highlights_subtitle", parent=base["BodyText"], fontName=fonts["body"], fontSize=10.5, leading=15, alignment=TA_CENTER, textColor=COLORS["soft_grey"], spaceAfter=4),
        "highlight_heading": ParagraphStyle("highlight_heading", parent=base["Heading3"], fontName=fonts["body_bold"], fontSize=10.5, leading=13, textColor=COLORS["gold"], spaceAfter=3),
        "highlight_value": ParagraphStyle("highlight_value", parent=base["BodyText"], fontName=fonts["body_bold"], fontSize=10, leading=13.5, textColor=COLORS["dark"], spaceAfter=4),
        "highlight_body": ParagraphStyle("highlight_body", parent=base["BodyText"], fontName=fonts["body"], fontSize=9.8, leading=13.8, textColor=COLORS["body"], spaceAfter=0),
        "hotel_name": ParagraphStyle("hotel_name", parent=base["Heading3"], fontName=fonts["heading"], fontSize=15, leading=18, textColor=COLORS["gold"], spaceAfter=3),
        "hotel_meta": ParagraphStyle("hotel_meta", parent=base["BodyText"], fontName=fonts["body_bold"], fontSize=10.2, leading=14, textColor=COLORS["dark"], spaceAfter=3),
        "hotel_body": ParagraphStyle("hotel_body", parent=base["BodyText"], fontName=fonts["body"], fontSize=9.8, leading=13.5, textColor=COLORS["body"], spaceAfter=4),
        "policy_title": ParagraphStyle("policy_title", parent=base["Heading2"], fontName=fonts["heading"], fontSize=20, leading=25, alignment=TA_CENTER, textColor=COLORS["dark"], spaceAfter=8),
        "policy_intro": ParagraphStyle("policy_intro", parent=base["BodyText"], fontName=fonts["body"], fontSize=10, leading=14, alignment=TA_CENTER, textColor=COLORS["soft_grey"], spaceAfter=4),
        "policy_card_title": ParagraphStyle("policy_card_title", parent=base["Heading3"], fontName=fonts["body_bold"], fontSize=10.2, leading=13, textColor=COLORS["dark"], spaceAfter=3),
        "policy_card_body": ParagraphStyle("policy_card_body", parent=base["BodyText"], fontName=fonts["body"], fontSize=8.8, leading=11.5, textColor=COLORS["body"], spaceAfter=0),
        "policy_price": ParagraphStyle("policy_price", parent=base["BodyText"], fontName=fonts["body_bold"], fontSize=9.2, leading=12, textColor=COLORS["gold"], spaceAfter=2),
        "policy_badge": ParagraphStyle("policy_badge", parent=base["BodyText"], fontName=fonts["body_bold"], fontSize=7.8, leading=10, textColor=COLORS["gold"], spaceAfter=2),
        "policy_number": ParagraphStyle("policy_number", parent=base["BodyText"], fontName=fonts["heading"], fontSize=14, leading=17, textColor=COLORS["gold"], spaceAfter=2),
    }
