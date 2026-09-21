"""
PDF rendering: policy pages (Things To Do, Payment, Cancellation, T&C, Inclusions, Payment Details).
"""
from io import BytesIO
from pathlib import Path

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
    _render_policy_page_title(story, styles, "THINGS TO DO IN ANDAMAN", "Signature Andaman Islands experiences curated for an elevated journey.")
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


def _agreement_styles(styles: dict[str, ParagraphStyle]):
    s_title = ParagraphStyle(
        "agr_title",
        parent=styles["day_title"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#111827"),
        alignment=1,  # Centered
        spaceAfter=14,
    )
    s_preamble = ParagraphStyle(
        "agr_preamble",
        parent=styles["body"],
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#374151"),
        spaceAfter=12,
    )
    s_sec_title = ParagraphStyle(
        "agr_sec_title",
        parent=styles["policy_card_title"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceBefore=10,
        spaceAfter=4,
    )
    s_sec_intro = ParagraphStyle(
        "agr_sec_intro",
        parent=styles["body"],
        fontSize=8.2,
        leading=11.8,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=6,
    )
    s_bullet = ParagraphStyle(
        "agr_bullet",
        parent=styles["body"],
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor("#374151"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=5,
    )
    s_sub_bullet = ParagraphStyle(
        "agr_sub_bullet",
        parent=styles["body"],
        fontSize=8.0,
        leading=11.0,
        textColor=colors.HexColor("#4B5563"),
        leftIndent=26,
        firstLineIndent=-10,
        spaceAfter=3,
    )
    return s_title, s_preamble, s_sec_title, s_sec_intro, s_bullet, s_sub_bullet


def render_payment_policy_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest = None) -> None:
    from datetime import date as _date
    story.append(PageBreak())
    s_title, s_preamble, s_sec_title, s_sec_intro, s_bullet, s_sub_bullet = _agreement_styles(styles)

    eff_date = _date.today().strftime("%B %d, %Y")
    client_name = escape_text(str(request.customer_name if request else "Valued Client") or "Valued Client")
    client_addr = escape_text(str(request.customer_nationality or request.customer_email if request else "Client Address") or "Client Address")

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Travel Agency Payment Agreement", s_title))

    preamble_text = (
        f"This Travel Agency Payment Agreement (\"Agreement\") is made effective as of <b>{eff_date}</b> "
        f"by and between <b>Andaman Islands Darun Tours and Travels</b>, a duly licensed travel agency with its principal "
        f"office located at <b>Andaman Islands, India</b> (\"Agency\"), and <b>{client_name}</b>, "
        f"with a mailing address of <b>{client_addr}</b> (\"Client\"). The purpose of this Agreement is to define the "
        f"financial terms and conditions pertaining to the travel services provided by the Agency to the Client."
    )
    story.append(Paragraph(preamble_text, s_preamble))

    story.append(Paragraph("1. Payment Terms", s_sec_title))
    story.append(Paragraph("In order to secure the comprehensive travel services provided by the Agency, the Client agrees to adhere to the following detailed payment structure:", s_sec_intro))

    story.append(Paragraph("• <b>Initial Deposit:</b> The Client is required to pay an initial deposit of 50% of the total estimated cost immediately upon confirming this booking. This deposit guarantees the reservation and allows the Agency to begin securing necessary bookings with airlines, hotels, inter-island ferries, and other service providers.", s_bullet))
    story.append(Paragraph("• <b>Final Payment:</b> The remaining 50% of the travel cost must be settled at least 30 days prior to the start of the travel (or upon arrival for short-notice reservations). This ensures that all services are paid in full and confirms all reservations in the Client's itinerary.", s_bullet))
    story.append(Paragraph("• <b>Payment Methods:</b> Payments can be made through several secure methods:", s_bullet))
    story.append(Paragraph("• <b>Bank Transfer:</b> Recommended for direct deposits from bank accounts (NEFT / RTGS / IMPS); might require standard banking processing time.", s_sub_bullet))
    story.append(Paragraph("• <b>UPI / QR Code:</b> For instant processing, immediate real-time verification, and booking confirmation.", s_sub_bullet))
    story.append(Paragraph("• <b>Cards &amp; Online Banking:</b> Acceptable via secure banking channels; must be cleared before final booking confirmation.", s_sub_bullet))
    story.append(Paragraph("• <b>Payment Instructions:</b> Detailed payment instructions, including official bank coordinates and a scan-to-pay QR code, are provided on the Payment Details schedule of this proposal.", s_bullet))

    story.append(Paragraph("2. Booking &amp; Confirmation Conditions", s_sec_title))
    story.append(Paragraph("The provision of travel arrangements is governed by the following operational conditions:", s_sec_intro))
    story.append(Paragraph("• <b>Tentative Reservations:</b> All hotel rooms, vehicle transfers, and ferry seats remain tentative until advance payment is received and formally acknowledged by the Agency.", s_bullet))
    story.append(Paragraph("• <b>Availability &amp; Rate Validity:</b> Services remain subject to operational availability. Quoted rates remain valid for 7 days from proposal date; statutory tax or tariff increases post-confirmation are payable by the Client.", s_bullet))
    story.append(Paragraph("• <b>Voucher &amp; Ticket Release:</b> Official hotel confirmation vouchers, inter-island ferry tickets, and activity permits are issued following settlement of payments.", s_bullet))


def render_cancellation_policy_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest = None) -> None:
    from datetime import date as _date
    story.append(PageBreak())
    s_title, s_preamble, s_sec_title, s_sec_intro, s_bullet, s_sub_bullet = _agreement_styles(styles)

    eff_date = _date.today().strftime("%B %d, %Y")
    client_name = escape_text(str(request.customer_name if request else "Valued Client") or "Valued Client")
    client_addr = escape_text(str(request.customer_nationality or request.customer_email if request else "Client Address") or "Client Address")

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Travel Agency Cancellation Agreement", s_title))

    preamble_text = (
        f"This Travel Agency Cancellation Agreement (\"Agreement\") is made effective as of <b>{eff_date}</b> "
        f"by and between <b>Andaman Islands Darun Tours and Travels</b>, a duly licensed travel agency with its principal "
        f"office located at <b>Andaman Islands, India</b> (\"Agency\"), and <b>{client_name}</b>, "
        f"with a mailing address of <b>{client_addr}</b> (\"Client\"). The purpose of this Agreement is to define "
        f"the cancellation timelines, supplier conditions, and refund terms pertaining to the travel services provided by the Agency to the Client."
    )
    story.append(Paragraph(preamble_text, s_preamble))

    story.append(Paragraph("1. Cancellation Schedule &amp; Fees", s_sec_title))
    story.append(Paragraph("In the event of cancellation of confirmed travel arrangements by the Client, the following structured cancellation timeline and charges shall strictly apply:", s_sec_intro))

    story.append(Paragraph("• <b>30+ Days Prior to Arrival:</b> A nominal 10% administrative and file processing charge applies. The remaining 90% is refundable subject to third-party supplier terms.", s_bullet))
    story.append(Paragraph("• <b>20 to 29 Days Prior to Arrival:</b> A cancellation charge of 50% of the total tour package cost applies.", s_bullet))
    story.append(Paragraph("• <b>Less than 20 Days Prior to Arrival:</b> A 100% cancellation charge applies (strictly non-refundable).", s_bullet))
    story.append(Paragraph("• <b>No-Show / Unannounced Absence:</b> 100% cancellation fee applies with zero refund in case of absence on travel date.", s_bullet))

    story.append(Paragraph("2. Supplier Policies &amp; Refund Terms", s_sec_title))
    story.append(Paragraph("Cancellations and amendments are subject to the following contractual conditions:", s_sec_intro))

    story.append(Paragraph("• <b>Peak Season Bookings:</b> Reservations falling between December 15 and January 15 (Christmas &amp; New Year), long holiday weekends, and festive dates are 100% non-refundable once confirmed.", s_bullet))
    story.append(Paragraph("• <b>Carrier &amp; Ferry Policies:</b> Inter-island ferry services (Makruzz, Green Ocean, Nautika, DSS) and flight bookings follow the respective carrier cancellation and refund rules.", s_bullet))
    story.append(Paragraph("• <b>Unused Services:</b> No refund or credit is issued for unused room nights, missed sightseeing, untaken meals, or unavailed sea activities.", s_bullet))
    story.append(Paragraph("• <b>Force Majeure Disruptions:</b> The Agency is not liable for weather-induced ferry cancellations, flight delays, or administrative beach closures. Rescheduling will be arranged subject to availability.", s_bullet))
    story.append(Paragraph("• <b>Refund Settlement Timeline:</b> Eligible and approved refunds are processed within 15 to 30 working days following supplier reconciliation.", s_bullet))


def render_terms_conditions_pages(story: list, styles: dict[str, ParagraphStyle], request: TripRequest = None) -> None:
    from datetime import date as _date
    story.append(PageBreak())
    s_title, s_preamble, s_sec_title, s_sec_intro, s_bullet, s_sub_bullet = _agreement_styles(styles)

    eff_date = _date.today().strftime("%B %d, %Y")
    client_name = escape_text(str(request.customer_name if request else "Valued Client") or "Valued Client")
    client_addr = escape_text(str(request.customer_nationality or request.customer_email if request else "Client Address") or "Client Address")

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Travel Agency Terms and Conditions Agreement", s_title))

    preamble_text = (
        f"This Travel Agency Terms and Conditions Agreement (\"Agreement\") is made effective as of <b>{eff_date}</b> "
        f"by and between <b>Andaman Islands Darun Tours and Travels</b>, a duly licensed travel agency with its principal "
        f"office located at <b>Andaman Islands, India</b> (\"Agency\"), and <b>{client_name}</b>, "
        f"with a mailing address of <b>{client_addr}</b> (\"Client\"). The purpose of this Agreement is to establish the "
        f"contractual terms, operational guidelines, and mutual responsibilities governing the travel services provided by the Agency."
    )
    story.append(Paragraph(preamble_text, s_preamble))

    story.append(Paragraph("1. Accommodation &amp; Transportation Guidelines", s_sec_title))
    story.append(Paragraph("The Client agrees to the following terms governing lodging, vehicles, and maritime transit:", s_sec_intro))

    story.append(Paragraph("• <b>Hotel Substitution:</b> If a confirmed hotel becomes unavailable due to overbooking, maintenance, or operational constraints, a property of equal or superior category shall be provided.", s_bullet))
    story.append(Paragraph("• <b>Check-In and Check-Out:</b> Hotel check-in (12:00 PM) and check-out (08:00 AM / 09:00 AM) timings are strictly governed by hotel policies. Early check-in or late check-out is subject to room availability.", s_bullet))
    story.append(Paragraph("• <b>Transportation Protocol:</b> Private air-conditioned vehicle transfers operate point-to-point as per the approved sightseeing plan and are not available for non-itinerary leisure transit.", s_bullet))
    story.append(Paragraph("• <b>Ferry &amp; Sea Movements:</b> Inter-island ferry and boat transfers remain subject to weather, operating conditions, and Port Management Board directives. Schedules may be altered in the interest of passenger safety.", s_bullet))

    story.append(Paragraph("2. Documentation, Liability &amp; Acceptance", s_sec_title))
    story.append(Paragraph("The provision of services is subject to regulatory compliance and liability boundaries:", s_sec_intro))

    story.append(Paragraph("• <b>Mandatory Travel Documents:</b> Indian nationals must carry original government-issued photo ID (Aadhaar/Passport/Voter ID). Foreign nationals must possess valid Passports and Indian Visas.", s_bullet))
    story.append(Paragraph("• <b>Personal Luggage &amp; Valuables:</b> The Agency assumes no liability for lost, stolen, or damaged baggage, cameras, or personal valuables during transfers and activities.", s_bullet))
    story.append(Paragraph("• <b>Limitation of Liability:</b> The Agency acts as an authorized travel coordinator and accepts no liability for personal injury, third-party operational deficiencies, delays, or natural calamities.", s_bullet))
    story.append(Paragraph("• <b>Binding Agreement:</b> Remittance of payment or commencement of tour services constitutes complete and irrevocable acceptance of all terms, conditions, and policies set forth herein.", s_bullet))


def render_payment_cancellation_policy_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest = None) -> None:
    render_payment_policy_page(story, styles, request)
    render_cancellation_policy_page(story, styles, request)



def render_inclusions_exclusions_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    story.append(PageBreak())
    _render_policy_page_title(story, styles, "INCLUSIONS & EXCLUSIONS", "A concise service summary for guest review and confirmation.")
    column_width = (PAGE_INNER_WIDTH - 14) / 2
    
    inclusion_list = []
    if hasattr(request, "included_activities") and request.included_activities:
        for act in request.included_activities:
            qty = getattr(act, "quantity", 1)
            name = getattr(act, "activity_name", str(act))
            if qty > 0:
                qty_str = f"{qty}x " if qty > 1 else ""
                inclusion_list.append(f"Complimentary Activity: {qty_str}{name}")
    inclusion_list.extend(INCLUSION_ITEMS)

    inclusions = _icon_list_card("INCLUSIONS", "✓", inclusion_list, styles, column_width, COLORS["card"])
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
        Paragraph(escape_text("ANDAMAN DARUN TOURS AND TRAVELS"), styles["body"]),
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
        Image(str(Path(__file__).resolve().parents[6] / "assets" / "images" / "qr_code.jpeg"), width=1.95 * inch, height=1.95 * inch, kind="proportional"),
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
        ("Andaman Islands Darun Tour and Travels", "body"),
        ("Phone", "label"),
        ("+91 9474238991", "body"),
        ("+91 9933242718", "body"),
    ]:
        story.append(Paragraph(escape_text(text), styles[style_name]))


def render_invoice_page(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    """
    Dedicated Travel Package Billing / Invoice Page.
    Minimalist, professional, clean layout matching real-world corporate travel invoices.
    - Header: 'Travel Package' + 'INVOICE' (left) | Company details (right)
    - Client Info + Invoice Metadata with clean neutral dividers
    - Services Table: Plain design with subtle zebra rows and clean borders (no blue/gold)
    - Totals: Clean SUBTOTAL | TAX (5% GST) | GRAND TOTAL band (no blue/gold boxes)
    - Currency: 'Rs.' to prevent missing glyphs
    """
    from datetime import date as _date

    # ── Neutral Minimalist Palette ─────────────────────────────
    C_DARK     = colors.HexColor("#1F2937")  # primary text / dark charcoal
    C_MUTED    = colors.HexColor("#6B7280")  # secondary / metadata labels (medium grey)
    C_LIGHT    = colors.HexColor("#9CA3AF")  # subtle / caption text
    C_LINE     = colors.HexColor("#E5E7EB")  # light subtle divider line
    C_LINE_D   = colors.HexColor("#D1D5DB")  # table header/footer boundary line
    C_ROW_ALT  = colors.HexColor("#F9FAFB")  # soft alternating row background
    C_WHITE    = colors.white

    W = PAGE_INNER_WIDTH

    # ─────────────────────────────────────────────────────────────────
    # DATA PIPELINE — DO NOT MODIFY THESE LINES
    # ─────────────────────────────────────────────────────────────────
    client_name       = str(request.customer_name or "Valued Guest").strip()
    client_email      = str(request.customer_email or "—").strip()
    client_phone      = str(request.customer_phone_number or "—").strip()
    client_nat        = str(request.customer_nationality or "—").strip()
    n_adults          = int(request.number_of_adults or 0)
    n_children        = int(request.number_of_children or 0)
    n_infants         = int(getattr(request, "number_of_infants", 0) or 0)
    n_seniors         = int(getattr(request, "number_of_senior_citizens", 0) or 0)
    destination       = str(request.destination or "Andaman Islands").strip()
    arrival           = str(request.arrival_date or "—").strip()
    departure         = str(request.departure_date or "—").strip()
    trip_type         = str(request.trip_type or "Leisure").strip()
    n_nights          = int(request.number_of_nights or 0)
    meal_plan         = str(request.meal_plan or "As Per Selection").strip()
    flight_opt        = str(request.flight_option or "Excluded").strip()
    flight_rate       = float(request.flight_per_person_rate or 0)
    transfer_type     = str(request.transfer_type or "—").strip()
    hotel_cat         = str(request.hotel_category_preference or "—").strip()
    activities        = list(request.preferred_activities or [])
    pp_cost           = float(request.per_person_cost or 0)
    child_cost        = float(getattr(request, "child_cost", 0) or 0)
    infant_cost       = float(getattr(request, "infant_cost", 0) or 0)
    senior_cost       = float(getattr(request, "senior_cost", 0) or 0)
    total_cost        = float(request.total_package_cost or 0)
    lead_id           = str(request.lead_id or "").strip()
    # ─────────────────────────────────────────────────────────────────

    # Derived display values (formatting only — no logic change)
    invoice_no   = f"ADT-{lead_id[:6].upper()}" if lead_id else f"ADT-{_date.today().strftime('%y%m%d')}"
    invoice_date = _date.today().strftime("%d %b %Y")
    duration_txt = f"{arrival}  →  {departure}" if arrival != "—" else "As Per Booking"
    pricing_tiers = getattr(request, "pricing_tiers", None) or []
    has_tiered   = bool(pricing_tiers or n_children > 0 or n_infants > 0 or n_seniors > 0)
    pax_total    = n_adults + n_children + n_infants + n_seniors
    if pricing_tiers:
        calc_package_sum = sum(
            float(t.get("pax", 1) if isinstance(t, dict) else getattr(t, "pax", 1)) *
            float(t.get("cost", 0.0) if isinstance(t, dict) else getattr(t, "cost", 0.0))
            for t in pricing_tiers
        )
    else:
        calc_package_sum = (n_adults * pp_cost) + (n_children * child_cost) + (n_infants * infant_cost) + (n_seniors * senior_cost)
    flight_sum   = (flight_rate * pax_total) if flight_opt and flight_opt.lower() != "excluded" else 0

    # 1. Determine pure tour package cost (land package: hotels, transfers, sightseeing, activities)
    if pricing_tiers and calc_package_sum > 0:
        pure_package_cost = calc_package_sum
    elif has_tiered and calc_package_sum > 0:
        pure_package_cost = calc_package_sum
    elif pp_cost > 0 and pax_total > 0 and not has_tiered:
        pure_package_cost = pp_cost * pax_total
    elif total_cost > 0:
        if flight_sum > 0 and total_cost > flight_sum:
            pure_package_cost = total_cost - flight_sum
        else:
            pure_package_cost = total_cost
    elif calc_package_sum > 0:
        pure_package_cost = calc_package_sum
    else:
        pure_package_cost = 0

    # 2. Total service subtotal (pure package + air transportation)
    total_service_subtotal = pure_package_cost + flight_sum

    # 3. 5% GST is calculated ONLY on the included tour package cost (NEVER on airfare)
    if pure_package_cost > 0:
        tax_amount  = round(pure_package_cost * 0.05)
        grand_total = total_service_subtotal + tax_amount
        sub_str     = f"Rs. {total_service_subtotal:,.0f}"
        tax_str     = f"Rs. {tax_amount:,.0f}"
        grand_str   = f"Rs. {grand_total:,.0f}"
    elif total_service_subtotal > 0:
        tax_amount  = 0
        grand_total = total_service_subtotal
        sub_str     = f"Rs. {total_service_subtotal:,.0f}"
        tax_str     = "—"
        grand_str   = f"Rs. {grand_total:,.0f}"
    else:
        tax_amount  = 0
        grand_total = 0
        sub_str     = "As Per Quote"
        tax_str     = "5% GST"
        grand_str   = "As Per Quote"

    def fmt_inr(v: float) -> str:
        return f"Rs. {v:,.0f}" if v > 0 else "As Per Quote"

    # ── Local paragraph styles ─────────────────────────────────
    def _style(name, parent_key, **kw):
        return ParagraphStyle(name, parent=styles[parent_key], **kw)

    s_co_name    = _style("inv_co_name",   "day_title",        fontSize=12.5, leading=16, textColor=C_DARK, alignment=2)
    s_co_info    = _style("inv_co_info",   "policy_card_body", fontSize=8,  leading=12, textColor=C_MUTED, alignment=2)
    s_heading    = _style("inv_heading",   "day_title",        fontSize=26, leading=30, textColor=C_DARK)
    s_sub        = _style("inv_sub",       "policy_card_title",fontSize=10, leading=13, textColor=C_MUTED, letterSpacing=2)
    s_meta_label = _style("inv_ml",        "label",            fontSize=7.5, leading=10, textColor=C_MUTED)
    s_meta_val   = _style("inv_mv",        "policy_card_body", fontSize=8.5, leading=11, textColor=C_DARK, alignment=2)
    s_cl_name    = _style("inv_cl_name",   "policy_card_title",fontSize=11, leading=14, textColor=C_DARK)
    s_cl_info    = _style("inv_cl_info",   "policy_card_body", fontSize=8.5, leading=12, textColor=C_MUTED)
    s_th         = _style("inv_th",        "policy_card_title",fontSize=8.5, leading=11, textColor=C_DARK, letterSpacing=0.5)
    s_th_r       = _style("inv_th_r",      "policy_card_title",fontSize=8.5, leading=11, textColor=C_DARK, letterSpacing=0.5, alignment=2)
    s_td_label   = _style("inv_td_l",      "policy_card_title",fontSize=9,  leading=13, textColor=C_DARK)
    s_td_desc    = _style("inv_td_d",      "policy_card_body", fontSize=8.5,leading=13, textColor=C_MUTED)
    s_td_rate    = _style("inv_td_rate",   "policy_card_body", fontSize=8.5,leading=13, textColor=C_DARK, alignment=2)
    s_td_amt     = _style("inv_td_amt",    "policy_price",     fontSize=9,  leading=13, textColor=C_DARK, alignment=2)
    s_tot_h      = _style("inv_tot_h",     "policy_card_title",fontSize=8.5, leading=11, textColor=C_MUTED, letterSpacing=0.5)
    s_tot_h_r    = _style("inv_tot_h_r",   "policy_card_title",fontSize=8.5, leading=11, textColor=C_MUTED, letterSpacing=0.5, alignment=2)
    s_tot_v      = _style("inv_tot_v",     "policy_card_title",fontSize=10.5,leading=14, textColor=C_DARK)
    s_grand_v    = _style("inv_gv",        "day_title",        fontSize=15, leading=19, textColor=C_DARK, alignment=2)
    s_footer     = _style("inv_footer",    "fine",             fontSize=7.5,leading=10, textColor=C_LIGHT)

    # ═══════════════════════════════════════════════════════════
    # SECTION 1 — HEADER BAND
    # Left: "Travel Package" heading + INVOICE label
    # Right: Company block
    # ═══════════════════════════════════════════════════════════
    left_header = [
        Paragraph("Travel Package", s_heading),
        Spacer(1, 4),
        Paragraph("INVOICE", s_sub),
    ]
    right_header = [
        Paragraph("ANDAMAN DARUN TOURS AND TRAVELS", s_co_name),
        Spacer(1, 4),
        Paragraph("Andaman Islands, India", s_co_info),
        Paragraph("andamandaruntourandtravels@gmail.com", s_co_info),
        Paragraph("+91 94742 38991  |  +91 99332 42718", s_co_info),
        Paragraph("www.andamandaruntourism.in", s_co_info),
    ]
    header_table = Table(
        [[left_header, right_header]],
        colWidths=[W * 0.46, W * 0.54],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
    ]))
    story.append(Spacer(1, 0.08 * inch))
    story.append(header_table)
    story.append(Spacer(1, 0.12 * inch))
    story.append(HRFlowable(width="100%", thickness=0.8, color=C_LINE))
    story.append(Spacer(1, 0.14 * inch))

    # ═══════════════════════════════════════════════════════════
    # SECTION 2 — CLIENT INFO  +  INVOICE META
    # ═══════════════════════════════════════════════════════════
    pax_parts = []
    if n_adults > 0:
        pax_parts.append(f"{n_adults} Adult{'s' if n_adults != 1 else ''}")
    if n_children > 0:
        pax_parts.append(f"{n_children} Child{'ren' if n_children > 1 else ''}")
    if n_infants > 0:
        pax_parts.append(f"{n_infants} Infant{'s' if n_infants != 1 else ''}")
    if n_seniors > 0:
        pax_parts.append(f"{n_seniors} Senior{'s' if n_seniors != 1 else ''}")
    pax_str = "  +  ".join(pax_parts) if pax_parts else f"{pax_total} Guests"

    client_block = [
        Paragraph(escape_text(client_name), s_cl_name),
        Spacer(1, 5),
        Paragraph(escape_text(client_email), s_cl_info),
        Paragraph(escape_text(client_phone), s_cl_info),
        Paragraph(escape_text(client_nat), s_cl_info),
        Paragraph(pax_str, s_cl_info),
    ]

    def _meta_row(label: str, value: str) -> list:
        return [
            Paragraph(escape_text(label), s_meta_label),
            Paragraph(escape_text(value),  s_meta_val),
        ]

    meta_rows = [
        _meta_row("Invoice Number", invoice_no),
        _meta_row("Date",           invoice_date),
        _meta_row("Destination",    destination),
        _meta_row("Duration",       duration_txt),
        _meta_row("Trip Type",      trip_type),
    ]
    meta_table = Table(
        meta_rows,
        colWidths=[W * 0.22, W * 0.26],
    )
    meta_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.3, C_LINE),
    ]))

    client_meta_table = Table(
        [[client_block, meta_table]],
        colWidths=[W * 0.50, W * 0.50],
    )
    client_meta_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN",         (1, 0), (1, 0),   "RIGHT"),
    ]))
    story.append(client_meta_table)
    story.append(Spacer(1, 0.16 * inch))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_LINE))
    story.append(Spacer(1, 0.14 * inch))

    # ═══════════════════════════════════════════════════════════
    # SECTION 3 — SERVICES TABLE (PLAIN, MINIMALIST)
    # Columns: Service | Description | Rate | Amount
    # ═══════════════════════════════════════════════════════════
    col_svc  = W * 0.22
    col_desc = W * 0.38
    col_rate = W * 0.20
    col_amt  = W * 0.20

    # Table header
    svc_header = [
        Paragraph("Service",     s_th),
        Paragraph("Description", s_th),
        Paragraph("Rate",        s_th_r),
        Paragraph("Amount",      s_th_r),
    ]

    # Build line items
    line_items = []

    # — Hotel / Accommodation
    if hotel_cat and hotel_cat != "—":
        hotel_nights = f"{n_nights} Night{'s' if n_nights != 1 else ''}" if n_nights > 0 else "As Booked"
        line_items.append(("Accommodation", f"{hotel_cat}  ·  {hotel_nights}", "Included in Package", "—"))

    # — Flight
    if flight_opt and flight_opt.lower() != "excluded":
        flight_desc = f"Round Trip  ·  {flight_opt}"
        flight_rate_str = fmt_inr(flight_rate) + " / Person" if flight_rate > 0 else "Included in Package"
        flight_amt_str  = fmt_inr(flight_rate * pax_total) if flight_rate > 0 and pax_total > 0 else "—"
        line_items.append(("Air Transportation", flight_desc, flight_rate_str, flight_amt_str))

    # — Transfer
    if transfer_type and transfer_type != "—":
        line_items.append(("Transfers", transfer_type, "Included in Package", "—"))

    # — Meal Plan
    if meal_plan and meal_plan != "—":
        line_items.append(("Meal Plan", meal_plan, "Included in Package", "—"))

    # — Activities (top 3 to keep it clean)
    top_acts = activities[:3]
    if top_acts:
        acts_desc = ",  ".join(top_acts)
        line_items.append(("Activities", escape_text(acts_desc), "Included in Package", "—"))

    # — Complimentary Included Activities
    if hasattr(request, "included_activities") and request.included_activities:
        comp_acts = []
        for act in request.included_activities:
            qty = getattr(act, "quantity", 1)
            name = getattr(act, "activity_name", str(act))
            if qty > 0:
                qty_str = f"{qty}x " if qty > 1 else ""
                comp_acts.append(f"{qty_str}{name}")
        if comp_acts:
            line_items.append(("Complimentary Activities", escape_text(", ".join(comp_acts)), "Complimentary (Free)", "Included"))

    # — Tour Guide / Manager
    line_items.append(("Tour Management", "Dedicated Tour Manager & Guide", "Included in Package", "—"))

    # — Package Cost
    if pricing_tiers:
        cat_labels = {
            "adult": "Adults",
            "child": "Child",
            "infant": "Infant",
            "senior": "Senior",
        }
        desc_lines = []
        rate_lines = []
        for t in pricing_tiers:
            pax = int(t.get("pax", 1) if isinstance(t, dict) else getattr(t, "pax", 1))
            cost = float(t.get("cost", 0.0) if isinstance(t, dict) else getattr(t, "cost", 0.0))
            cat = str(t.get("category", "adult") if isinstance(t, dict) else getattr(t, "category", "adult"))
            label_val = str(t.get("label", "") if isinstance(t, dict) else getattr(t, "label", "") or "")
            custom_label = label_val or cat_labels.get(cat, cat.title())
            desc_lines.append(f"Per Person ({custom_label})  ×  {pax:02d} Pax")
            rate_str = f"{fmt_inr(cost)} / Person" if cost > 0 else ("Complimentary" if cat == "infant" else ("As Per Quote" if cat in ("adult", "senior") else "Included in Package"))
            rate_lines.append(rate_str)

        amt_str = fmt_inr(calc_package_sum) if calc_package_sum > 0 else (fmt_inr(pure_package_cost) if pure_package_cost > 0 else "—")
        line_items.append(("Package Cost", desc_lines, rate_lines, amt_str))
    elif has_tiered:
        desc_lines = []
        rate_lines = []
        if n_adults > 0:
            desc_lines.append(f"Per Person (Adults)  ×  {n_adults:02d} Pax")
            rate_lines.append(f"{fmt_inr(pp_cost)} / Person" if pp_cost > 0 else "As Per Quote")
        if n_children > 0:
            desc_lines.append(f"Per Person (Child)  ×  {n_children:02d} Pax")
            rate_lines.append(f"{fmt_inr(child_cost)} / Person" if child_cost > 0 else "Included in Package")
        if n_infants > 0:
            desc_lines.append(f"Per Person (Infant)  ×  {n_infants:02d} Pax")
            rate_lines.append(f"{fmt_inr(infant_cost)} / Person" if infant_cost > 0 else "Complimentary")
        if n_seniors > 0:
            desc_lines.append(f"Per Person (Senior)  ×  {n_seniors:02d} Pax")
            rate_lines.append(f"{fmt_inr(senior_cost)} / Person" if senior_cost > 0 else "As Per Quote")
        amt_str = fmt_inr(calc_package_sum) if calc_package_sum > 0 else (fmt_inr(pure_package_cost) if pure_package_cost > 0 else "—")
        line_items.append(("Package Cost", desc_lines, rate_lines, amt_str))
    else:
        pp_rate_str = fmt_inr(pp_cost) + " / Person" if pp_cost > 0 else "As Per Quote"
        pp_amt_str  = fmt_inr(pp_cost * pax_total) if pp_cost > 0 and pax_total > 0 else (fmt_inr(total_cost) if total_cost > 0 else "As Per Quote")
        line_items.append(("Package Cost", f"Per Person  ×  {pax_total:02d} Pax", pp_rate_str, pp_amt_str))

    # Build rows
    def _svc_row(svc, desc, rate, amt):
        desc_list = desc if isinstance(desc, list) else [desc]
        rate_list = rate if isinstance(rate, list) else [rate]
        
        desc_paras = [Paragraph(escape_text(d), s_td_desc) for d in desc_list]
        rate_paras = [Paragraph(escape_text(r), s_td_rate) for r in rate_list]
        
        return [
            [Paragraph(escape_text(svc),  s_td_label)],
            desc_paras,
            rate_paras,
            [Paragraph(escape_text(amt),  s_td_amt)],
        ]

    svc_data = [svc_header]
    for svc, desc, rate, amt in line_items:
        svc_data.append(_svc_row(svc, desc, rate, amt))

    n_rows = len(svc_data)
    svc_ts = [
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        # Clean header dividers — no blue fill, no gold line
        ("BACKGROUND",    (0, 0), (-1, 0), C_WHITE),
        ("LINEABOVE",     (0, 0), (-1, 0), 1.0, C_LINE_D),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.0, C_LINE_D),
        # Subtle alternating row fills
        *[("BACKGROUND", (0, i), (-1, i), C_ROW_ALT if i % 2 == 0 else C_WHITE) for i in range(1, n_rows)],
        # Subtle row dividers
        *[("LINEBELOW", (0, i), (-1, i), 0.3, C_LINE) for i in range(1, n_rows - 1)],
        # Clean bottom line
        ("LINEBELOW",     (0, -1), (-1, -1), 1.0, C_LINE_D),
    ]

    svc_table = Table(svc_data, colWidths=[col_svc, col_desc, col_rate, col_amt])
    svc_table.setStyle(TableStyle(svc_ts))
    story.append(svc_table)
    story.append(Spacer(1, 0.20 * inch))

    # ═══════════════════════════════════════════════════════════
    # SECTION 4 — TOTALS BAND (PLAIN, MINIMALIST)
    # SUBTOTAL | TAX (5% GST) | GRAND TOTAL
    # ═══════════════════════════════════════════════════════════
    col_t = W / 3

    totals_header = [
        Paragraph("SUBTOTAL",     s_tot_h),
        Paragraph("TAX (5% GST)", s_tot_h),
        Paragraph("GRAND TOTAL",  s_tot_h_r),
    ]
    totals_values = [
        Paragraph(sub_str,   s_tot_v),
        Paragraph(tax_str,   s_tot_v),
        Paragraph(grand_str, s_grand_v),
    ]

    totals_table = Table(
        [totals_header, totals_values],
        colWidths=[col_t, col_t, col_t],
    )
    totals_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        # Clean boundary lines — no blue fill, no gold borders
        ("BACKGROUND",    (0, 0), (-1, -1), C_WHITE),
        ("LINEABOVE",     (0, 0), (-1, 0), 1.0, C_LINE_D),
        ("LINEBELOW",     (0, 1), (-1, 1), 1.0, C_LINE_D),
    ]))
    story.append(totals_table)

    # ═══════════════════════════════════════════════════════════
    # SECTION 5 — FOOTER
    # ═══════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.22 * inch))
    story.append(HRFlowable(width="100%", thickness=0.6, color=C_LINE))
    story.append(Spacer(1, 0.08 * inch))
    footer_left  = Paragraph("www.andamandaruntourism.in", s_footer)
    footer_right = Paragraph("andamandaruntourandtravels@gmail.com", ParagraphStyle(
        "inv_footer_r", parent=s_footer, alignment=2
    ))
    footer_table = Table([[footer_left, footer_right]], colWidths=[W * 0.5, W * 0.5])
    footer_table.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(footer_table)


def render_terms_pages(story: list, styles: dict[str, ParagraphStyle], request: TripRequest) -> None:
    story.append(PageBreak())
    render_invoice_page(story, styles, request)
    render_payment_details_page(story, styles)
    render_inclusions_exclusions_page(story, styles, request)
    render_cancellation_policy_page(story, styles, request)
    render_payment_policy_page(story, styles, request)
    render_terms_conditions_pages(story, styles, request)

