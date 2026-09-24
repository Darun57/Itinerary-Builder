"""
Velqairn Canonical Proposal Document Builder
============================================
Constructs an authoritative ProposalDocument IR from a TripRequest and generated itinerary text.

Architectural Guarantees:
- ProposalDocument is the Single Source of Truth.
- Sections store logical section_id and order; physical pages are derived via PagePlan.
- Strict provenance tracking via ProposalValue.
- Separation of AgencyContext from DestinationContext.
- Semantic image slot assignments that fail closed.
- Mathematical pricing invariants (subtotal + tax = grand_total).
- Explicit DependencyGraph registration.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.proposal import (
    AgencyContextData,
    BankAccountDetails,
    ChangeState,
    ContentClassification,
    CoverContent,
    DayScheduleBullet,
    DependencyGraph,
    DestinationContextData,
    HighlightCard,
    HighlightsContent,
    HotelStayItem,
    ImageAsset,
    ImageCrop,
    ImageFocalPoint,
    ImageSourceType,
    ImageVerificationStatus,
    InclusionsExclusionsContent,
    InvoiceContent,
    ItineraryDayContent,
    LayoutBlock,
    LuxuryStaysContent,
    PagePlan,
    PaymentDetailsContent,
    PhysicalPage,
    PolicyAgreementContent,
    PolicyClause,
    PricingLineItem,
    ProposalDocument,
    ProposalSection,
    ProposalValidationReport,
    ProposalValue,
    SectionType,
    SemanticImageSlot,
    SourceType,
    StructuredPricing,
)
from app.schemas.trip import TripRequest
from app.services.destination_registry import (
    AGENCY_CONTEXT,
    get_destination_context,
    is_andaman_destination,
    load_capabilities,
    load_destinations,
    load_movements,
    normalize_region,
)
from app.services.pdf.constants import (
    CANCELLATION_DETAIL_CARDS,
    CANCELLATION_TIMELINE,
    EXCLUSION_ITEMS,
    INCLUSION_ITEMS,
    PAYMENT_POLICY_CARDS,
    TERMS_CONDITION_CARDS,
)
from app.services.pdf.day_parser import split_itinerary_into_days
from app.services.pdf.highlight_builder import highlight_sections
from app.services.pdf.image_resolver import resolve_day_image, resolve_namespace_image
from app.services.pdf.sections.hotels import _consolidate_hotel_stays, _lookup_hotel_metadata
from app.services.pdf.text_utils import extract_trip_title, sanitize_itinerary_text


def _resolve_image_asset(
    destination_id: str,
    label: str,
    source_type: ImageSourceType = ImageSourceType.DESTINATION_CATALOG,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> Optional[ImageAsset]:
    """
    Resolve image path and wrap in ImageAsset.
    Fails closed: NEVER leaks cross-destination images.
    """
    clean_dest = destination_id.lower().strip()
    is_andaman = is_andaman_destination(clean_dest)
    
    img_path = None
    if is_andaman:
        from app.services.image_loader import get_destination_image_paths, get_cover_image_path
        if "cover" in label.lower():
            img_path = get_cover_image_path()
        else:
            candidates = get_destination_image_paths(label)
            if candidates:
                img_path = candidates[0]
    else:
        # Non-Andaman destination: strictly search within destination images namespace
        if "cover" in label.lower():
            from app.services.destination_registry import DESTINATION_ROOT
            try:
                norm = normalize_region(clean_dest)
                dest_img_dir = DESTINATION_ROOT / norm / "images"
                for ext in ("jpg", "jpeg", "png", "webp"):
                    candidate = dest_img_dir / f"cover.{ext}"
                    if candidate.exists():
                        img_path = candidate
                        break
            except Exception:
                img_path = None
        else:
            img_path = resolve_namespace_image(clean_dest, label)

    if not img_path:
        return None

    return ImageAsset(
        image_id=f"img_{uuid.uuid4().hex[:8]}",
        source_type=source_type,
        verification_status=ImageVerificationStatus.VERIFIED,
        destination_id=clean_dest,
        entity_type=entity_type or "destination",
        entity_id=entity_id or f"{clean_dest}:{label.lower().replace(' ', '_')}",
        path_or_url=str(img_path),
        alt_text=f"{label} in {destination_id.title()}",
        caption=label,
        crop=ImageCrop(),
        focal_point=ImageFocalPoint(),
        fit_mode="cover",
    )


def derive_page_plan(sections: List[ProposalSection]) -> PagePlan:
    """
    Derives physical PDF pages from logical sections.
    Logical sections are NOT 1:1 with physical pages.
    """
    pages: List[PhysicalPage] = []
    current_page_idx = 1

    for section in sorted(sections, key=lambda s: s.order):
        if not section.enabled:
            continue

        # Each enabled section allocates its estimated_pages
        sec_pages = max(1, section.estimated_pages)
        for p in range(sec_pages):
            block = LayoutBlock(
                block_id=f"blk_{section.id}_{p+1}",
                section_id=section.id,
                block_type=section.type.value,
                estimated_height_pt=841.89,  # A4 height
                can_split=False,
            )
            physical_page = PhysicalPage(
                page_index=current_page_idx,
                section_ids=[section.id],
                blocks=[block],
                estimated_height_pt=841.89,
                is_full_page_break=True,
            )
            pages.append(physical_page)
            current_page_idx += 1

    return PagePlan(pages=pages, total_pages=len(pages))


def build_proposal_document_from_trip(
    request: TripRequest,
    itinerary_text: str = "",
) -> ProposalDocument:
    """
    Constructs an authoritative ProposalDocument from a TripRequest and AI text.
    """
    raw_dest = (request.destination or "").strip()
    if not raw_dest and request.selected_destinations:
        raw_dest = request.selected_destinations[0].strip()
    if not raw_dest:
        raw_dest = "Goa"

    dest_norm = "andaman" if is_andaman_destination(raw_dest) else normalize_region(raw_dest)
    dest_ctx = get_destination_context(dest_norm, request)

    # 1. Separate Contexts
    destination_context = DestinationContextData(
        destination_id=dest_norm,
        display_name=dest_ctx.display_name,
        is_andaman=dest_ctx.is_andaman,
        has_verified_ferry_movement=dest_ctx.has_verified_ferry_movement,
        entry_hub=dest_ctx.entry_hub,
        capabilities={},
    )
    try:
        if not dest_ctx.is_andaman:
            destination_context.capabilities = load_capabilities(dest_norm)
    except Exception:
        destination_context.capabilities = {}

    agency_context = AgencyContextData(
        brand_name="Andaman Darun Tours and Travels" if dest_ctx.is_andaman else "Darun Tourism",
        legal_name=dest_ctx.agency_legal_name,
        location=dest_ctx.agency_location,
        email=dest_ctx.agency_email,
        website=dest_ctx.agency_website,
        phone_numbers=[AGENCY_CONTEXT.phone_primary, AGENCY_CONTEXT.phone_secondary],
        bank_account_name="ANDAMAN DARUN TOURS AND TRAVELS" if dest_ctx.is_andaman else "DARUN TOURISM",
        bank_name=AGENCY_CONTEXT.bank_name,
        account_number=AGENCY_CONTEXT.account_number,
        ifsc=AGENCY_CONTEXT.ifsc,
        branch=AGENCY_CONTEXT.upi_branch,
        proprietor=AGENCY_CONTEXT.proprietor_name,
    )

    dep_graph = DependencyGraph()
    sections: List[ProposalSection] = []
    order_idx = 1

    # 2. Section: Cover
    cleaned_itinerary = sanitize_itinerary_text(itinerary_text)
    trip_title = extract_trip_title(cleaned_itinerary, dest_ctx.display_name)
    cover_hero_asset = _resolve_image_asset(dest_norm, "cover", ImageSourceType.DESTINATION_CATALOG)
    cover_image_slot = SemanticImageSlot(
        slot_id="cover.hero",
        label="Cover Hero Image",
        asset=cover_hero_asset,
        fallback_policy="generic_abstract_or_none",
    )
    
    nights = request.number_of_nights or max(1, (request.number_of_days or 4) - 1)
    days = request.number_of_days or (nights + 1)
    duration_str = f"{nights} Nights / {days} Days"

    cover_section = ProposalSection(
        id="sec_cover",
        type=SectionType.COVER,
        title="Cover Page",
        display_title=f"{dest_ctx.display_name} Proposal",
        classification=ContentClassification.USER_EDITABLE,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=CoverContent(
            proposal_title=ProposalValue.from_source(trip_title, SourceType.SYSTEM_GENERATED),
            proposal_subtitle=ProposalValue.from_source(f"{duration_str} Exclusive Journey", SourceType.SYSTEM_GENERATED),
            destination_display=dest_ctx.display_name,
            duration_text=duration_str,
            customer_name=request.customer_name or "Valued Guest",
            package_type=request.budget_category or "Premium Luxury",
        ),
        images=[cover_image_slot],
        dependencies=[f"destination:{dest_norm}"],
        estimated_pages=1,
    )
    sections.append(cover_section)
    order_idx += 1

    # 3. Section: Trip Highlights
    highlight_data_cards = highlight_sections(cleaned_itinerary, request)
    hl_cards: List[HighlightCard] = []
    for idx, card in enumerate(highlight_data_cards):
        card_val = card.get("value", "")
        card_desc = card.get("description", "") or card.get("body", "")
        hl_cards.append(HighlightCard(
            card_id=f"card_{idx+1}",
            title=card.get("title", ""),
            value=ProposalValue.from_source(card_val, SourceType.AI_GENERATED),
            description=ProposalValue.from_source(card_desc, SourceType.AI_GENERATED),
        ))

    highlights_section = ProposalSection(
        id="sec_highlights",
        type=SectionType.TRIP_HIGHLIGHTS,
        title="Trip Highlights",
        display_title="Trip Highlights",
        classification=ContentClassification.USER_EDITABLE,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=HighlightsContent(
            headline="TRIP HIGHLIGHTS",
            subheadline="A curated overview of your selected guest journey.",
            cards=hl_cards,
        ),
        images=[],
        dependencies=[f"destination:{dest_norm}"],
        estimated_pages=1,
    )
    sections.append(highlights_section)
    order_idx += 1

    # 4. Section: Luxury Stays
    raw_stays = _consolidate_hotel_stays(request)
    stay_items: List[HotelStayItem] = []
    stay_hotel_ids: List[str] = []

    for stay in raw_stays:
        h_name = stay.get("hotel_name", "").strip()
        h_nights = stay.get("nights", 1)
        h_meta = _lookup_hotel_metadata(h_name, None, destination=dest_norm)
        hotel_node_id = f"hotel:{h_name.lower().replace(' ', '_')}"
        stay_hotel_ids.append(hotel_node_id)

        hotel_img = _resolve_image_asset(
            dest_norm,
            h_name,
            source_type=ImageSourceType.HOTEL_CATALOG,
            entity_type="hotel",
            entity_id=hotel_node_id,
        )
        h_slot = SemanticImageSlot(
            slot_id=f"{hotel_node_id}.hero",
            label=f"{h_name} Image",
            asset=hotel_img,
            fallback_policy="generic_abstract_or_none",
        )

        stay_items.append(HotelStayItem(
            hotel_id=hotel_node_id,
            hotel_name=ProposalValue.from_source(h_name, SourceType.CATALOG_DEFAULT, source_ref=hotel_node_id),
            location=ProposalValue.from_source(h_meta.get("location", dest_ctx.display_name), SourceType.CATALOG_DEFAULT),
            star_category=ProposalValue.from_source(h_meta.get("category", "Luxury"), SourceType.CATALOG_DEFAULT),
            room_type=ProposalValue.from_source(h_meta.get("room_type", "Standard Room"), SourceType.CATALOG_DEFAULT),
            nights=h_nights,
            description=ProposalValue.from_source(h_meta.get("description", ""), SourceType.CATALOG_DEFAULT),
            image_slot=h_slot,
        ))

    stays_section = ProposalSection(
        id="sec_luxury_stays",
        type=SectionType.LUXURY_STAYS,
        title="Luxury Stays",
        display_title="Your Luxury Accommodations",
        classification=ContentClassification.DATA_DERIVED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=LuxuryStaysContent(
            headline="YOUR LUXURY STAYS",
            subheadline="Hand-picked accommodations tailored to your comfort.",
            stays=stay_items,
        ),
        images=[s.image_slot for s in stay_items if s.image_slot],
        dependencies=[f"destination:{dest_norm}"] + stay_hotel_ids,
        estimated_pages=1 if len(stay_items) <= 3 else 2,
    )
    sections.append(stays_section)
    order_idx += 1

    # Register Stays dependencies in graph
    for h_id in stay_hotel_ids:
        dep_graph.register_dependency(h_id, "sec_luxury_stays")
        dep_graph.register_dependency(h_id, "sec_highlights")

    # 5. Section: Itinerary Days
    raw_days = split_itinerary_into_days(cleaned_itinerary)
    total_days_count = len(raw_days) if raw_days else days

    used_images_set = set()
    for d_idx in range(1, total_days_count + 1):
        day_raw = raw_days[d_idx - 1] if d_idx <= len(raw_days) else {}
        day_sec_id = f"sec_day_{d_idx}"
        
        # Location & hotel for day
        day_island = str(day_raw.get("primary_island") or day_raw.get("island") or dest_ctx.display_name).strip()
        day_title_val = str(day_raw.get("title") or f"Day {d_idx} in {day_island}").strip()
        day_route_val = str(day_raw.get("route") or day_raw.get("travel_movement") or day_island).strip()
        is_dep = bool(day_raw.get("is_departure_day")) or (d_idx == total_days_count)

        # Day image
        day_img_path = resolve_day_image(request, d_idx, used_images=used_images_set, is_final_day=is_dep)
        day_hero_asset = None
        if day_img_path:
            used_images_set.add(day_img_path)
            day_hero_asset = ImageAsset(
                image_id=f"img_day_{d_idx}",
                source_type=ImageSourceType.DESTINATION_CATALOG,
                verification_status=ImageVerificationStatus.VERIFIED,
                destination_id=dest_norm,
                entity_type="day",
                entity_id=f"day_{d_idx}",
                path_or_url=str(day_img_path),
                alt_text=f"Day {d_idx} - {day_title_val}",
                caption=day_title_val,
                crop=ImageCrop(),
                focal_point=ImageFocalPoint(),
                fit_mode="cover",
            )

        day_hero_slot = SemanticImageSlot(
            slot_id=f"day.{d_idx}.hero",
            label=f"Day {d_idx} Hero Image",
            asset=day_hero_asset,
            fallback_policy="generic_abstract_or_none",
        )

        # Bullets
        bullets: List[DayScheduleBullet] = []
        raw_items = day_raw.get("items") or []
        b_idx = 1
        for itm in raw_items:
            paras = itm.get("paragraphs") or []
            b_list = itm.get("bullets") or []
            label = itm.get("label") or ""
            for p in paras:
                text_content = f"{label}: {p}" if label else p
                bullets.append(DayScheduleBullet(
                    bullet_id=f"b_{d_idx}_{b_idx}",
                    text=ProposalValue.from_source(text_content, SourceType.AI_GENERATED),
                    is_subitem=bool(itm.get("is_subitem", False)),
                ))
                b_idx += 1
            for b in b_list:
                text_content = f"{label}: {b}" if (label and not b.startswith(label)) else b
                bullets.append(DayScheduleBullet(
                    bullet_id=f"b_{d_idx}_{b_idx}",
                    text=ProposalValue.from_source(text_content, SourceType.AI_GENERATED),
                    is_subitem=bool(itm.get("is_subitem", False)),
                ))
                b_idx += 1

        plan_match = next((p for p in (request.daily_island_plan or []) if p.day_number == d_idx), None)
        if not bullets and plan_match:
            for time_slot, slot_val in [
                ("Morning", getattr(plan_match, "morning", "")),
                ("Afternoon", getattr(plan_match, "afternoon", "")),
                ("Evening", getattr(plan_match, "evening", "")),
                ("Night", getattr(plan_match, "night", "")),
            ]:
                if slot_val:
                    bullets.append(DayScheduleBullet(
                        bullet_id=f"b_{d_idx}_{b_idx}",
                        text=ProposalValue.from_source(f"{time_slot}: {slot_val}", SourceType.AI_GENERATED),
                        is_subitem=False,
                    ))
                    b_idx += 1
        if not bullets:
            bullets.append(DayScheduleBullet(
                bullet_id=f"b_{d_idx}_1",
                text=ProposalValue.from_source(f"Curated exploration and sightseeing in {day_island}.", SourceType.AI_GENERATED),
                is_subitem=False,
            ))

        # Day hotel dependency
        day_dependencies = [f"destination:{dest_norm}"]
        if plan_match and plan_match.hotel:
            h_node = f"hotel:{plan_match.hotel.lower().replace(' ', '_')}"
            day_dependencies.append(h_node)
            dep_graph.register_dependency(h_node, day_sec_id)

        day_section = ProposalSection(
            id=day_sec_id,
            type=SectionType.ITINERARY_DAY,
            title=f"Day {d_idx}: {day_title_val}",
            display_title=f"Day {d_idx} — {day_island}",
            classification=ContentClassification.USER_EDITABLE,
            change_state=ChangeState.CLEAN,
            enabled=True,
            order=order_idx,
            content=ItineraryDayContent(
                day_number=d_idx,
                date_str=f"Day {d_idx}",
                location_title=day_island,
                title=ProposalValue.from_source(day_title_val, SourceType.AI_GENERATED),
                subtitle=ProposalValue.from_source(day_route_val, SourceType.AI_GENERATED),
                hero_image=day_hero_slot,
                gallery_images=[],
                visiting_places_story=ProposalValue.from_source(str(day_raw.get("summary_intro") or ""), SourceType.AI_GENERATED),
                todays_journey=ProposalValue.from_source(day_route_val, SourceType.AI_GENERATED),
                schedule_bullets=bullets,
                hotel_experience=ProposalValue.from_source("Relaxation and premium leisure at your reserved stay.", SourceType.AI_GENERATED),
                is_departure_day=is_dep,
                attractions=list(day_raw.get("attractions") or []),
                activities=list(day_raw.get("activities") or []),
            ),
            images=[day_hero_slot] if day_hero_slot else [],
            dependencies=day_dependencies,
            estimated_pages=1,
        )
        sections.append(day_section)
        order_idx += 1

    # 6. Section: Invoice & Structured Pricing
    base_cost = float(request.total_package_cost or 0.0)
    if base_cost <= 0:
        adults = max(1, request.number_of_adults or 2)
        rate = float(request.per_person_cost or 45000.0)
        base_cost = adults * rate

    line_items: List[PricingLineItem] = [
        PricingLineItem(
            item_id="li_package_base",
            category="accommodation",
            description=f"Curated {dest_ctx.display_name} Private Package ({duration_str})",
            quantity=1,
            unit_price=base_cost,
            subtotal=base_cost,
            is_taxable=True,
        )
    ]
    if request.flight_option == "Included" and request.flight_per_person_rate > 0:
        flight_sub = request.flight_per_person_rate * max(1, request.number_of_adults or 1)
        line_items.append(PricingLineItem(
            item_id="li_airfare",
            category="transfers",
            description="Domestic Airfare Supplement",
            quantity=max(1, request.number_of_adults or 1),
            unit_price=request.flight_per_person_rate,
            subtotal=flight_sub,
            is_taxable=True,
        ))

    pricing = StructuredPricing(
        currency="INR",
        line_items=line_items,
        pure_package_cost=base_cost,
        subtotal=sum(i.subtotal for i in line_items),
        tax_rate=0.05,
    )
    pricing.recalculate()

    invoice_section = ProposalSection(
        id="sec_invoice",
        type=SectionType.INVOICE,
        title="Tax Invoice",
        display_title="Booking Summary & Proforma Invoice",
        classification=ContentClassification.DATA_DERIVED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=InvoiceContent(
            invoice_number=f"INV-{dest_norm.upper()}-{uuid.uuid4().hex[:6].upper()}",
            invoice_date=datetime.now(timezone.utc).strftime("%d %b %Y"),
            duration_text=duration_str,
            trip_type=request.trip_type or "Curated Leisure",
            client_name=request.customer_name or "Valued Guest",
            client_email=request.customer_email or "guest@daruntourism.in",
            client_phone=request.customer_phone_number or "+91 0000000000",
            client_nationality=request.customer_nationality or "Indian",
            pax_summary=f"{request.number_of_adults or 2} Adults",
            pricing=pricing,
        ),
        images=[],
        dependencies=[f"destination:{dest_norm}", "pricing:package"] + stay_hotel_ids,
        estimated_pages=1,
    )
    sections.append(invoice_section)
    order_idx += 1

    # Register invoice dependencies in graph
    dep_graph.register_dependency("pricing:package", "sec_invoice")
    for h_id in stay_hotel_ids:
        dep_graph.register_dependency(h_id, "sec_invoice")

    # 7. Section: Payment Details (SYSTEM_LOCKED)
    payment_section = ProposalSection(
        id="sec_payment_details",
        type=SectionType.PAYMENT_DETAILS,
        title="Payment Details",
        display_title="Payment Information",
        classification=ContentClassification.SYSTEM_LOCKED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=PaymentDetailsContent(
            headline="PAYMENT DETAILS",
            subheadline="Statutory bank transfer details for booking confirmation.",
            bank_details=BankAccountDetails(
                account_name=agency_context.bank_account_name,
                bank_name=agency_context.bank_name,
                account_number=agency_context.account_number,
                ifsc=agency_context.ifsc,
                branch=agency_context.branch,
                proprietor=agency_context.proprietor,
                phone_numbers=agency_context.phone_numbers,
            ),
        ),
        images=[],
        dependencies=[],
        estimated_pages=1,
    )
    sections.append(payment_section)
    order_idx += 1

    # 8. Section: Inclusions & Exclusions (DATA_DERIVED)
    inclusions_section = ProposalSection(
        id="sec_inclusions_exclusions",
        type=SectionType.INCLUSIONS_EXCLUSIONS,
        title="Inclusions & Exclusions",
        display_title="Service Scope & Exclusions",
        classification=ContentClassification.DATA_DERIVED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=InclusionsExclusionsContent(
            headline="INCLUSIONS & EXCLUSIONS",
            subheadline="Clear scope of provided ground services and guest exclusions.",
            inclusions=[ProposalValue.from_source(item, SourceType.SYSTEM_GENERATED) for item in INCLUSION_ITEMS],
            exclusions=[ProposalValue.from_source(item, SourceType.SYSTEM_GENERATED) for item in EXCLUSION_ITEMS],
        ),
        images=[],
        dependencies=[f"destination:{dest_norm}"],
        estimated_pages=1,
    )
    sections.append(inclusions_section)
    order_idx += 1

    # 9. Section: Cancellation (SYSTEM_LOCKED)
    cancel_clauses = [
        PolicyClause(
            clause_id=f"c_time_{idx}",
            heading=t[0],
            text=ProposalValue.from_source(f"{t[1]} — {t[2]}", SourceType.SYSTEM_GENERATED),
            bullets=[],
        )
        for idx, t in enumerate(CANCELLATION_TIMELINE)
    ]
    for c_title, c_text in CANCELLATION_DETAIL_CARDS:
        if "ferry" in c_title.lower() or "ferry" in c_text.lower():
            if not destination_context.has_verified_ferry_movement:
                continue
        cancel_clauses.append(PolicyClause(
            clause_id=f"c_detail_{len(cancel_clauses)}",
            heading=c_title,
            text=ProposalValue.from_source(c_text, SourceType.SYSTEM_GENERATED),
            bullets=[],
        ))
    if destination_context.has_verified_ferry_movement:
        cancel_clauses.append(PolicyClause(
            clause_id="c_carrier_ferry",
            heading="Carrier & Ferry Policies",
            text=ProposalValue.from_source(
                "Inter-island ferry services (Makruzz, Green Ocean, Nautika, DSS) and flight bookings follow the respective carrier cancellation and refund rules.",
                SourceType.SYSTEM_GENERATED,
            ),
            bullets=[],
        ))
    cancellation_section = ProposalSection(
        id="sec_cancellation",
        type=SectionType.CANCELLATION,
        title="Cancellation Policy",
        display_title="Cancellation & Refund Terms",
        classification=ContentClassification.SYSTEM_LOCKED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=PolicyAgreementContent(
            agreement_title="CANCELLATION & REFUND POLICY",
            effective_date=datetime.now(timezone.utc).strftime("%d %b %Y"),
            agency_legal_name=agency_context.legal_name,
            agency_location=agency_context.location,
            client_name=request.customer_name or "Valued Guest",
            client_address=request.customer_country or "India",
            preamble="The following cancellation terms apply to all confirmed bookings.",
            clauses=cancel_clauses,
        ),
        images=[],
        dependencies=[],
        estimated_pages=1,
    )
    sections.append(cancellation_section)
    order_idx += 1

    # 10. Section: Payment Agreement (SYSTEM_LOCKED)
    payment_clauses = [
        PolicyClause(
            clause_id=f"c_pay_{idx}",
            heading=c[0],
            text=ProposalValue.from_source(c[1], SourceType.SYSTEM_GENERATED),
            bullets=[],
        )
        for idx, c in enumerate(PAYMENT_POLICY_CARDS)
    ]
    payment_agreement_section = ProposalSection(
        id="sec_payment_agreement",
        type=SectionType.PAYMENT_AGREEMENT,
        title="Payment Agreement",
        display_title="Payment Terms & Confirmation Schedule",
        classification=ContentClassification.SYSTEM_LOCKED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=PolicyAgreementContent(
            agreement_title="PAYMENT SCHEDULE AGREEMENT",
            effective_date=datetime.now(timezone.utc).strftime("%d %b %Y"),
            agency_legal_name=agency_context.legal_name,
            agency_location=agency_context.location,
            client_name=request.customer_name or "Valued Guest",
            client_address=request.customer_country or "India",
            preamble="Payment obligations and schedule for booking validity.",
            clauses=payment_clauses,
        ),
        images=[],
        dependencies=[],
        estimated_pages=1,
    )
    sections.append(payment_agreement_section)
    order_idx += 1

    # 11. Section: Terms & Conditions (SYSTEM_LOCKED)
    tc_clauses = []
    for idx, c in enumerate(TERMS_CONDITION_CARDS):
        if "ferry" in c[0].lower() or "ferry" in c[1].lower():
            if not destination_context.has_verified_ferry_movement:
                continue
        tc_clauses.append(PolicyClause(
            clause_id=f"c_tc_{idx}",
            heading=c[0],
            text=ProposalValue.from_source(c[1], SourceType.SYSTEM_GENERATED),
            bullets=[],
        ))
    if destination_context.has_verified_ferry_movement:
        regulator = "Port Management Board directives" if dest_ctx.is_andaman else "local maritime/administrative directives"
        tc_clauses.append(PolicyClause(
            clause_id="c_tc_ferry_regulator",
            heading="Ferry Operations & Marine Regulations",
            text=ProposalValue.from_source(
                f"Inter-island transfers are subject to weather, operational feasibility, and {regulator}.",
                SourceType.SYSTEM_GENERATED,
            ),
            bullets=[],
        ))
    terms_section = ProposalSection(
        id="sec_terms_conditions",
        type=SectionType.TERMS_CONDITIONS,
        title="Terms & Conditions",
        display_title="General Terms & Conditions",
        classification=ContentClassification.SYSTEM_LOCKED,
        change_state=ChangeState.CLEAN,
        enabled=True,
        order=order_idx,
        content=PolicyAgreementContent(
            agreement_title="STANDARD TERMS & CONDITIONS",
            effective_date=datetime.now(timezone.utc).strftime("%d %b %Y"),
            agency_legal_name=agency_context.legal_name,
            agency_location=agency_context.location,
            client_name=request.customer_name or "Valued Guest",
            client_address=request.customer_country or "India",
            preamble="General terms governing tour operations and supplier coordination.",
            clauses=tc_clauses,
        ),
        images=[],
        dependencies=[],
        estimated_pages=1,
    )
    sections.append(terms_section)
    order_idx += 1

    # 12. Derive Page Plan
    page_plan = derive_page_plan(sections)

    # 13. Construct ProposalDocument
    doc = ProposalDocument(
        id=f"prop_{uuid.uuid4().hex[:12]}",
        version="1.0.0",
        revision=1,
        trip_id=request.lead_id or "LEAD-AUTO",
        destination_id=dest_norm,
        destination_context=destination_context,
        agency_context=agency_context,
        day_wise_style=request.day_wise_style or "luxury_narrative",
        customer={
            "name": request.customer_name,
            "email": request.customer_email,
            "phone": request.customer_phone_number,
            "nationality": request.customer_nationality,
            "adults": request.number_of_adults,
            "children": request.number_of_children,
        },
        duration={
            "number_of_days": days,
            "number_of_nights": nights,
            "arrival_date": request.arrival_date,
            "departure_date": request.departure_date,
        },
        sections=sections,
        dependency_graph=dep_graph,
        pricing=pricing,
        page_plan=page_plan,
        validation=ProposalValidationReport(is_valid=True, can_render_pdf=True),
    )

    return doc
