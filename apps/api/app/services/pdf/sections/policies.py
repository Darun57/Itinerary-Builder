"""
PDF rendering: policy pages (Things To Do, Payment, Cancellation, T&C, Inclusions, Payment Details).
"""
from io import BytesIO

from PIL import Image as PILImage, ImageDraw
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import HRFlowable, Image, PageBreak, Paragraph, Spacer, Table, TableStyle

from app.schemas.trip import TripRequest
from app.services.pdf.constants import (
    COLORS, PAGE_INNER_WIDTH,
    THINGS_TO_DO_CATEGORIES, PAYMENT_POLICY_CARDS, CANCELLATION_TIMELINE,
    CANCELLATION_DETAIL_CARDS, TERMS_CONDITION_CARDS, INCLUSION_ITEMS, EXCLUSION_ITEMS,
)
from app.services.pdf.text_utils import escape_text


def _render_policy_page_title(story: list, styles: dict[str, ParagraphStyle], title: str, subtitle: str) -> None:
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(escape_text(title), styles["policy_title"]))
    story.append(Paragraph(escape_text(subtitle), styles["policy_intro"]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(HRFlowable(width="24%", thickness=1.0, color=COLORS["gold"], hAlign="CENTER"))
    story.append(Spacer(1, 0.2 * inch))


def _card_table(content: list, width: float, background=None) -> Table:
    if background is None:
        background = COLORS["card"]
    table = Table([[content]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.65, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def _blank_reserve_box(width: float, height: float) -> Table:
    table = Table([[""]], colWidths=[width], rowHeights=[height])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["soft_white"]),
        ("BOX", (0, 0), (-1, -1), 0.7, COLORS["line"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _build_payment_qr_image() -> BytesIO:
    width = height = 900
    image = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)
    border = 80
    draw.rounded_rectangle((border, border, width - border, height - border), radius=36, outline="#c8a96a", width=14, fill="#fbfaf7")
    cell = 64
    offset = 150
    modules = ["1111111", "1000001", "1011101", "1011101", "1011101", "1000001", "1111111"]
    for row_index, row in enumerate(modules):
        for col_index, char in enumerate(row):
            if char == "1":
                x0 = offset + col_index * cell
                y0 = offset + row_index * cell
                draw.rectangle((x0, y0, x0 + cell - 10, y0 + cell - 10), fill="#10202d")
                draw.rectangle((x0 + 18, y0 + 18, x0 + cell - 28, y0 + cell - 28), fill="#c8a96a")
    draw.text((250, 640), "DARUN", fill="#10202d")
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def _render_card_grid(story: list, cards: list, columns: int = 2, gap: float = 12) -> None:
    card_width = (PAGE_INNER_WIDTH - gap * (columns - 1)) / columns
    rows = []
    for index in range(0, len(cards), columns):
        row = cards[index: index + columns]
        while len(row) < columns:
            row.append(Spacer(1, 0.01 * inch))
        rows.append(row)
    table = Table(rows, colWidths=[card_width] * columns, hAlign="CENTER")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gap / 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(table)


def _icon_list_card(title: str, icon: str, items: list[str], styles: dict[str, ParagraphStyle], width: float, background) -> Table:
    content = [
        Paragraph(escape_text(title), styles["policy_card_title"]),
        HRFlowable(width="100%", thickness=0.45, color=COLORS["gold"]),
        Spacer(1, 0.08 * inch),
    ]
    for item in items:
        content.append(Paragraph(escape_text(f"{icon} {item}"), styles["policy_card_body"]))
        content.append(Spacer(1, 0.05 * inch))
    return _card_table(content, width, background)


def render_things_to_do_page(story: list, styles: dict[str, ParagraphStyle]) -> None:
    _render_policy_page_title(story, styles, "THINGS TO DO IN ANDAMAN", "Signature island experiences curated for elevated Andaman journeys.")
    category_width = (PAGE_INNER_WIDTH - 14) / 2
    category_cards = []
    for category, items in THINGS_TO_DO_CATEGORIES:
        content = [
            Paragraph(escape_text(category), styles["policy_card_title"]),
            HRFlowable(width="100%", thickness=0.45, color=COLORS["gold"]),
            Spacer(1, 0.06 * inch),
        ]
        for name, price, description, is_new in items:
            content.append(Paragraph(escape_text(f"{'NEW  ' if is_new else ''}{name}"), styles["policy_card_title" if is_new else "policy_card_body"]))
            content.append(Paragraph(escape_text(f"Starting from {price}"), styles["policy_price"]))
            content.append(Paragraph(escape_text(description), styles["policy_card_body"]))
            content.append(Spacer(1, 0.06 * inch))
        category_cards.append(_card_table(content, category_width))
    _render_card_grid(story, category_cards, columns=2, gap=14)
    story.append(_card_table(
        [Paragraph(escape_text("All activities are subject to weather conditions, operational feasibility, safety guidelines, and permissions granted by the concerned authorities."), styles["policy_card_body"])],
        PAGE_INNER_WIDTH, COLORS["soft_white"]
    ))
    story.append(PageBreak())


def render_payment_cancellation_policy_page(story: list, styles: dict[str, ParagraphStyle]) -> None:
    # ── PAGE 1: PAYMENT POLICY ────────────────────────────────────────────────
    _render_policy_page_title(story, styles, "PAYMENT POLICY", "Transparent payment terms and booking conditions for your reservation.")

    card_width_2 = (PAGE_INNER_WIDTH - 10) / 2
    payment_cards = [
        _card_table(
            [Paragraph(escape_text(title), styles["policy_card_title"]), Spacer(1, 0.04 * inch), Paragraph(escape_text(body), styles["policy_card_body"])],
            card_width_2, COLORS["soft_white"] if index % 2 else COLORS["card"]
        )
        for index, (title, body) in enumerate(PAYMENT_POLICY_CARDS)
    ]
    _render_card_grid(story, payment_cards, columns=2, gap=10)
    story.append(PageBreak())

    # ── PAGE 2: CANCELLATION POLICY ───────────────────────────────────────────
    _render_policy_page_title(story, styles, "CANCELLATION POLICY", "Cancellation timelines, supplier conditions, and refund terms.")

    # Section A: Timeline (4-column, same as before)
    timeline_width = (PAGE_INNER_WIDTH - 18) / 4
    timeline_cards = [
        _card_table(
            [Paragraph(escape_text(label), styles["policy_card_title"]), Spacer(1, 0.04 * inch), Paragraph(escape_text(charge), styles["policy_price"]), Spacer(1, 0.04 * inch), Paragraph(escape_text(body), styles["policy_card_body"])],
            timeline_width, COLORS["card"]
        )
        for label, charge, body in CANCELLATION_TIMELINE
    ]
    _render_card_grid(story, timeline_cards, columns=4, gap=6)
    story.append(Spacer(1, 0.18 * inch))

    # Section B: Cancellation detail cards (2-column)
    detail_width = (PAGE_INNER_WIDTH - 10) / 2
    detail_cards = [
        _card_table(
            [Paragraph(escape_text(title), styles["policy_card_title"]), Spacer(1, 0.04 * inch), Paragraph(escape_text(body), styles["policy_card_body"])],
            detail_width, COLORS["soft_white"] if index % 2 else COLORS["card"]
        )
        for index, (title, body) in enumerate(CANCELLATION_DETAIL_CARDS)
    ]
    _render_card_grid(story, detail_cards, columns=2, gap=10)
    story.append(PageBreak())


def render_terms_conditions_pages(story: list, styles: dict[str, ParagraphStyle]) -> None:
    _render_policy_page_title(story, styles, "TERMS & CONDITIONS", "Essential travel terms presented for clarity before confirmation.")

    columns = 3
    gap = 8
    card_width = (PAGE_INNER_WIDTH - gap * (columns - 1)) / columns
    fixed_row_height = 1.05 * inch   # Uniform height enforced for every row

    style_term_title = ParagraphStyle(
        "tc_card_title",
        parent=styles["policy_card_title"],
        fontSize=9.5,
        leading=12,
        spaceAfter=3,
    )
    style_term_body = ParagraphStyle(
        "tc_card_body",
        parent=styles["policy_card_body"],
        fontSize=8.0,
        leading=10.2,
    )

    n_rows = (len(TERMS_CONDITION_CARDS) + columns - 1) // columns
    rows = []
    for r in range(n_rows):
        row_cells = []
        for c in range(columns):
            idx = r * columns + c
            if idx < len(TERMS_CONDITION_CARDS):
                num = idx + 1
                title, body = TERMS_CONDITION_CARDS[idx]
                row_cells.append([
                    Paragraph(escape_text(f"{num:02d}. {title}"), style_term_title),
                    Paragraph(escape_text(body), style_term_body),
                ])
            else:
                row_cells.append([""])
        rows.append(row_cells)

    ts = [
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("INNERGRID",     (0, 0), (-1, -1), 0.55, COLORS["line"]),
        ("BOX",           (0, 0), (-1, -1), 0.55, COLORS["line"]),
    ]
    for r in range(n_rows):
        for c in range(columns):
            idx = r * columns + c
            bg = COLORS["card"] if idx % 2 == 0 else COLORS["soft_white"]
            ts.append(("BACKGROUND", (c, r), (c, r), bg))

    grid = Table(
        rows,
        colWidths=[card_width] * columns,
        rowHeights=[fixed_row_height] * n_rows,
        hAlign="CENTER",
    )
    grid.setStyle(TableStyle(ts))
    story.append(grid)
    story.append(PageBreak())



def render_inclusions_exclusions_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    _render_policy_page_title(story, styles, "INCLUSIONS & EXCLUSIONS", "A concise service summary for guest review and confirmation.")
    column_width = (PAGE_INNER_WIDTH - 14) / 2
    inclusions = _icon_list_card("INCLUSIONS", "✓", INCLUSION_ITEMS, styles, column_width, COLORS["card"])
    exclusions = _icon_list_card("EXCLUSIONS", "✗", EXCLUSION_ITEMS, styles, column_width, COLORS["soft_white"])
    table = Table([[inclusions, exclusions]], colWidths=[column_width, column_width], hAlign="CENTER")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.12 * inch))

    story.append(Spacer(1, 0.1 * inch))

    # --- ROW 1: MEAL PLAN ---
    meal_plan_val = str(request.meal_plan or "As Per Selection").upper().strip()
    row1_left = [
        Paragraph("MEAL PLAN INCLUDED", styles["policy_card_title"]),
        Paragraph("Selected dining plan for your itinerary stay.", styles["policy_card_body"]),
    ]
    row1_right = [
        Paragraph(escape_text(meal_plan_val), styles["policy_price"]),
    ]
    row1_table = Table([[row1_left, row1_right]], colWidths=[PAGE_INNER_WIDTH * 0.7, PAGE_INNER_WIDTH * 0.3])
    row1_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["card"]),
        ("BOX", (0, 0), (-1, -1), 0.65, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(row1_table)
    story.append(Spacer(1, 0.08 * inch))

    # --- ROW 2: FLIGHT DETAILS & PRICING ---
    flight_opt = str(request.flight_option or "Excluded").strip().upper()
    flight_rate = float(request.flight_per_person_rate or 0)
    rate_text = f"₹ {flight_rate:,.0f} / Person" if flight_rate > 0 else "As Per Quote"

    row2_left = [
        Paragraph(escape_text(f"FLIGHT DETAILS  •  STATUS: {flight_opt}"), styles["policy_card_title"]),
        Paragraph("Round-trip airfare per guest (Up & Down).", styles["policy_card_body"]),
    ]
    row2_right = [
        Paragraph(escape_text(rate_text), styles["policy_price"]),
    ]
    row2_table = Table([[row2_left, row2_right]], colWidths=[PAGE_INNER_WIDTH * 0.7, PAGE_INNER_WIDTH * 0.3])
    row2_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["soft_white"]),
        ("BOX", (0, 0), (-1, -1), 0.65, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(row2_table)
    story.append(Spacer(1, 0.08 * inch))

    # --- ROW 3: PER PERSON COST ---
    pp_cost = float(request.per_person_cost or 0)
    pp_text = f"₹ {pp_cost:,.0f} / Person" if pp_cost > 0 else "As Per Quote"
    
    row3_left = [
        Paragraph("PER PERSON COST", styles["policy_card_title"]),
        Paragraph("Package cost per person.", styles["policy_card_body"]),
    ]
    row3_right = [
        Paragraph(escape_text(pp_text), styles["policy_price"]),
    ]
    row3_table = Table([[row3_left, row3_right]], colWidths=[PAGE_INNER_WIDTH * 0.7, PAGE_INNER_WIDTH * 0.3])
    row3_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["card"]),
        ("BOX", (0, 0), (-1, -1), 0.65, COLORS["line"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(row3_table)
    story.append(Spacer(1, 0.08 * inch))

    # --- ROW 4: TOTAL PACKAGE COST (Unique Luxury Navy & Gold Banner) ---
    pkg_cost = float(request.total_package_cost or 0)
    cost_text = f"₹ {pkg_cost:,.0f}" if pkg_cost > 0 else "As Per Quote"

    style_cost_title = ParagraphStyle(
        "cost_banner_title",
        parent=styles["policy_card_title"],
        fontSize=11,
        leading=14,
        textColor=COLORS["gold"],
    )
    style_cost_sub = ParagraphStyle(
        "cost_banner_sub",
        parent=styles["policy_card_body"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#94a3b8"),
    )
    style_cost_price = ParagraphStyle(
        "cost_banner_price",
        parent=styles["day_title"],
        fontSize=20,
        leading=24,
        alignment=TA_RIGHT,
        textColor=COLORS["gold"],
    )
    style_cost_note = ParagraphStyle(
        "cost_banner_note",
        parent=styles["fine"],
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#e2e8f0"),
    )

    row4_left = [
        Paragraph("TOTAL PACKAGE COST", style_cost_title),
        Paragraph("All-inclusive luxury package price for entire duration.", style_cost_sub),
    ]
    row4_right = [
        Paragraph(escape_text(cost_text), style_cost_price),
        Paragraph("Net Payable Amount", style_cost_note),
    ]
    row4_table = Table([[row4_left, row4_right]], colWidths=[PAGE_INNER_WIDTH * 0.55, PAGE_INNER_WIDTH * 0.45])
    row4_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORS["navy"]),
        ("BOX", (0, 0), (-1, -1), 1.2, COLORS["gold"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(row4_table)


def render_payment_details_page(story: list, styles: dict[str, ParagraphStyle]) -> None:
    story.append(PageBreak())
    _render_policy_page_title(story, styles, "PAYMENT DETAILS", "Secure payment information for your confirmed booking.")
    left_width = (PAGE_INNER_WIDTH - 14) * 0.58
    right_width = PAGE_INNER_WIDTH - left_width - 14

    left_content = [
        Paragraph(escape_text("ACCOUNT DETAILS"), styles["policy_card_title"]),
        HRFlowable(width="100%", thickness=0.45, color=COLORS["gold"]),
        Spacer(1, 0.06 * inch),
        Paragraph(escape_text("Account Name"), styles["label"]),
        Paragraph(escape_text("ANDAMAN DARUN TOUR AND TRAVELS"), styles["body"]),
        Spacer(1, 0.06 * inch),
        Paragraph(escape_text("Bank"), styles["label"]),
        Paragraph(escape_text("HDFC BANK"), styles["body"]),
        Spacer(1, 0.06 * inch),
        Paragraph(escape_text("Account Number"), styles["label"]),
        Paragraph(escape_text("50200085886802 (CURRENT ACCOUNT)"), styles["body"]),
        Spacer(1, 0.06 * inch),
        Paragraph(escape_text("IFSC"), styles["label"]),
        Paragraph(escape_text("HDFC0009508"), styles["body"]),
        Spacer(1, 0.06 * inch),
        Paragraph(escape_text("Branch"), styles["label"]),
        Paragraph(escape_text("Bathubasti, Garacharma"), styles["body"]),
    ]
    left_card = _card_table(left_content, left_width, COLORS["card"])

    qr_content = [
        Paragraph(escape_text("PAY BY QR"), styles["policy_card_title"]),
        HRFlowable(width="100%", thickness=0.45, color=COLORS["gold"]),
        Spacer(1, 0.12 * inch),
        Image(r"C:\Users\darun\Downloads\company qr code.jpeg", width=1.95 * inch, height=1.95 * inch, kind="proportional"),
        Spacer(1, 0.08 * inch),
        Paragraph(escape_text("Scan to Pay"), styles["policy_card_title"]),
        Paragraph(escape_text("UPI / Bank Transfer Accepted"), styles["fine"]),
    ]
    right_card = _card_table(qr_content, right_width, COLORS["soft_white"])

    payment_table = Table([[left_card, right_card]], colWidths=[left_width, right_width], hAlign="CENTER")
    payment_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 0.18 * inch))
    story.append(HRFlowable(width="100%", thickness=0.75, color=COLORS["line"]))
    story.append(Spacer(1, 0.12 * inch))
    for text, style_name in [
        ("BEST REGARDS", "policy_card_title"),
        ("Hemawathi", "day_title"),
        ("Proprietor", "label"),
        ("Andaman Darun Tour and Travels", "body"),
        ("Phone", "label"),
        ("+91 9474238991", "body"),
        ("+91 9933242718", "body"),
    ]:
        story.append(Paragraph(escape_text(text), styles[style_name]))


def render_terms_pages(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    story.append(PageBreak())
    render_payment_cancellation_policy_page(story, styles)
    render_terms_conditions_pages(story, styles)
    render_inclusions_exclusions_page(story, styles, request)
    render_payment_details_page(story, styles)
