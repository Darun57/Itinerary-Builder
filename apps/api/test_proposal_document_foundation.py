"""
Phase 0 Foundation Test Suite: Canonical ProposalDocument IR
===========================================================
Validates:
1. Building ProposalDocument from Goa, Rajasthan, Kashmir, and Andaman TripRequests.
2. Derivation of physical pages from logical sections (PagePlan abstraction).
3. Provenance model (ProposalValue with source_type, source_ref, override).
4. Dependency graph registration and breadth-first target invalidation.
5. Structured pricing invariants (subtotal + tax = grand_total).
6. Separation of AgencyContext from DestinationContext.
7. Semantic image slots with verification status and destination boundary invariant.
8. 6-layer Preflight Validation contract.
9. Negative Contamination Tests:
   - Injected Port Blair into Goa day -> FAILS.
   - Injected Havelock image into Goa proposal -> FAILS.
   - Injected manufactured 'Goa Airport' -> FAILS.
   - Injected arbitrary free-typed grand total mismatch -> FAILS.
   - Injected tampered statutory bank details -> FAILS.
   - Injected unverified ferry into non-ferry destination -> FAILS.
10. Andaman Golden Regression:
   - Port Blair, Havelock, Veer Savarkar Airport, Cellular Jail preserved intact.
"""
import sys
import unittest
from pathlib import Path

# Ensure api directory is on path
API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.schemas.proposal import (
    ChangeState,
    ContentClassification,
    ImageAsset,
    ImageSourceType,
    ImageVerificationStatus,
    ProposalSection,
    ProposalValue,
    SectionType,
    SourceType,
)
from app.schemas.trip import DayPlan, TripRequest
from app.services.destination_registry import normalize_region
from app.services.proposal_builder import build_proposal_document_from_trip, derive_page_plan
from app.services.proposal_validator import validate_proposal_document


def create_trip_request(
    destination: str,
    days: int = 5,
    hotel: str = "Grand Resort",
    customer_name: str = "Aarav Sharma",
) -> TripRequest:
    nights = days - 1
    daily_plan = [
        DayPlan(
            day_number=i,
            primary_island=f"{destination} Central",
            hotel=hotel,
            morning=f"Morning exploration in {destination}",
            afternoon=f"Afternoon leisure in {destination}",
            evening=f"Sunset experience in {destination}",
            night=f"Dinner and stay at {hotel}",
        )
        for i in range(1, days + 1)
    ]
    return TripRequest(
        customer_name=customer_name,
        customer_email="aarav@example.com",
        customer_phone_number="+91 9876543210",
        destination=destination,
        number_of_days=days,
        number_of_nights=nights,
        number_of_adults=2,
        total_package_cost=90000.0,
        per_person_cost=45000.0,
        daily_island_plan=daily_plan,
        day_wise_style="luxury_narrative",
    )


class TestProposalDocumentFoundation(unittest.TestCase):
    """Proves Phase 0 Document Model across Goa, Rajasthan, Kashmir, and Andaman."""

    def test_builds_across_destinations(self):
        cases = [
            ("Goa", "Taj Exotica Resort & Spa"),
            ("Rajasthan", "The Oberoi Udaivilas"),
            ("Kashmir", "The Khyber Himalayan Resort"),
            ("Andaman", "Taj Exotica Resort & Spa, Andamans"),
        ]
        for destination, default_hotel in cases:
            with self.subTest(destination=destination):
                req = create_trip_request(destination=destination, hotel=default_hotel)
                sample_itinerary = f"""
                Day 1: Arrival in {destination}
                Welcome to your exclusive private journey.
                Day 2: Cultural Exploration
                Immerse yourself in authentic experiences.
                Day 3: Scenic Discoveries
                Discover picturesque landmarks.
                Day 4: Leisure & Local Flavours
                Relaxed day of shopping and culinary delights.
                Day 5: Departure
                Transfer to airport for your onward journey.
                """
                doc = build_proposal_document_from_trip(req, sample_itinerary)

                self.assertIsNotNone(doc)
                self.assertTrue(doc.id.startswith("prop_"))
                expected_dest_id = "andaman" if destination.lower() == "andaman" else normalize_region(destination)
                self.assertEqual(doc.destination_id, expected_dest_id)
                self.assertEqual(doc.destination_context.destination_id, expected_dest_id)
                self.assertGreaterEqual(len(doc.sections), 10)

                # Verify default required logical sections exist
                types = [s.type for s in doc.sections]
                self.assertIn(SectionType.COVER, types)
                self.assertIn(SectionType.TRIP_HIGHLIGHTS, types)
                self.assertIn(SectionType.LUXURY_STAYS, types)
                self.assertIn(SectionType.ITINERARY_DAY, types)
                self.assertIn(SectionType.INVOICE, types)
                self.assertIn(SectionType.PAYMENT_DETAILS, types)
                self.assertIn(SectionType.INCLUSIONS_EXCLUSIONS, types)
                self.assertIn(SectionType.CANCELLATION, types)
                self.assertIn(SectionType.PAYMENT_AGREEMENT, types)
                self.assertIn(SectionType.TERMS_CONDITIONS, types)

                # Separation of AgencyContext from DestinationContext
                self.assertTrue(bool(doc.agency_context.brand_name))
                self.assertTrue(bool(doc.agency_context.account_number))
                self.assertTrue(bool(doc.destination_context.display_name))

                # Preflight Validation on built document
                report = validate_proposal_document(doc)
                self.assertTrue(
                    report.is_valid,
                    f"Validation failed for {destination}: {[i.message for i in report.issues]}"
                )

    def test_sections_not_tied_permanently_to_physical_page_numbers(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Day 4 has its own section_id and order, but NOT a hardcoded page number field
        day_4_sec = next(s for s in doc.sections if s.id == "sec_day_4")
        self.assertFalse(hasattr(day_4_sec, "page_number"))
        self.assertGreater(day_4_sec.order, 0)

        # Physical page count is derived via page_plan
        self.assertGreaterEqual(doc.page_plan.total_pages, len(doc.sections))
        initial_total = doc.page_plan.total_pages

        # Simulate adding a custom 2-page gallery section before Day 4
        gallery = ProposalSection(
            id="sec_custom_gallery",
            type=SectionType.CUSTOM_GALLERY,
            title="Photo Gallery",
            display_title="Exclusive Gallery",
            classification=ContentClassification.USER_EDITABLE,
            order=day_4_sec.order - 1,
            content={},
            estimated_pages=2,
        )
        doc.sections.append(gallery)
        doc.page_plan = derive_page_plan(doc.sections)

        # Total pages dynamically grew without mutating Day 4's identity
        self.assertEqual(doc.page_plan.total_pages, initial_total + 2)

    def test_provenance_and_override_model(self):
        req = create_trip_request("Goa", hotel="Hotel Fidalgo")
        doc = build_proposal_document_from_trip(req)

        stays_sec = doc.get_section("sec_luxury_stays")
        hotel_item = stays_sec.content.stays[0]

        self.assertIsInstance(hotel_item.hotel_name, ProposalValue)
        self.assertEqual(hotel_item.hotel_name.value, "Hotel Fidalgo")
        self.assertFalse(hotel_item.hotel_name.is_overridden)

        # Employee overrides hotel presentation title
        hotel_item.hotel_name.set_override("Hotel Fidalgo — Executive Heritage Room", modifier="emp_darun_42")
        self.assertEqual(hotel_item.hotel_name.value, "Hotel Fidalgo — Executive Heritage Room")
        self.assertEqual(hotel_item.hotel_name.original_value, "Hotel Fidalgo")
        self.assertTrue(hotel_item.hotel_name.is_overridden)
        self.assertEqual(hotel_item.hotel_name.last_modified_by, "emp_darun_42")

        # Revert back to catalog source
        hotel_item.hotel_name.revert_to_source()
        self.assertEqual(hotel_item.hotel_name.value, "Hotel Fidalgo")
        self.assertFalse(hotel_item.hotel_name.is_overridden)

    def test_dependency_graph_and_invalidation(self):
        req = create_trip_request("Goa", days=5, hotel="Taj Fort Aguada")
        doc = build_proposal_document_from_trip(req)

        graph = doc.dependency_graph
        hotel_key = "hotel:taj_fort_aguada"
        invalidated = graph.get_invalidated_targets(hotel_key)

        # Invalidated targets MUST include stays, day sections that use this hotel, highlights, and invoice
        self.assertIn("sec_luxury_stays", invalidated)
        self.assertIn("sec_invoice", invalidated)
        self.assertIn("sec_highlights", invalidated)
        self.assertTrue(any("sec_day_" in tgt for tgt in invalidated))

    def test_structured_pricing_invariants(self):
        req = create_trip_request("Goa", days=5)
        doc = build_proposal_document_from_trip(req)

        pricing = doc.pricing
        self.assertEqual(pricing.pure_package_cost, 90000.0)
        self.assertEqual(pricing.subtotal, 90000.0)
        self.assertEqual(pricing.tax_amount, round(90000.0 * 0.05))
        self.assertEqual(pricing.grand_total, 90000.0 + round(90000.0 * 0.05))


class TestNegativeContaminationAndSecurityTests(unittest.TestCase):
    """Validates that the 6-layer validator FAILS CLOSED on any breach."""

    def test_inject_port_blair_into_goa_day_fails(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: inject Port Blair into Goa Day 2
        day_2 = doc.get_section("sec_day_2")
        day_2.content.schedule_bullets[0].text.value = "After breakfast, transfer to Port Blair harbor for sightseeing."

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "CONTAM_ANDAMAN_ENTITY_IN_NON_ANDAMAN_DAY" for i in report.issues))

    def test_inject_havelock_image_into_goa_proposal_fails(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: assign an Andaman image to Goa cover
        cover_sec = doc.get_section("sec_cover")
        cover_sec.images[0].asset = ImageAsset(
            image_id="img_havelock_sunset",
            source_type=ImageSourceType.DESTINATION_CATALOG,
            verification_status=ImageVerificationStatus.VERIFIED,
            destination_id="andaman",  # Mismatched destination
            entity_type="destination",
            entity_id="andaman:havelock",
            path_or_url="/images/andaman/havelock.jpg",
            alt_text="Havelock Sunset",
            caption="Sunset at Havelock",
        )

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "DEST_IMAGE_MISMATCH" for i in report.issues))

    def test_inject_manufactured_airport_fails(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: set manufactured "Goa Airport"
        doc.destination_context.entry_hub = "Goa Airport"

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "CONTAM_MANUFACTURED_AIRPORT" for i in report.issues))

    def test_inject_pricing_grand_total_mismatch_fails(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: arbitrary employee typed total
        doc.pricing.grand_total = 999999.0

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "FACT_PRICING_GRAND_TOTAL_MISMATCH" for i in report.issues))

    def test_inject_tampered_statutory_bank_account_fails(self):
        req = create_trip_request("Goa", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: override locked bank account in payment details
        pay_sec = doc.get_section("sec_payment_details")
        pay_sec.content.bank_details.account_number = "999999999999 (FAKE ACCOUNT)"

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "SEC_BANK_ACCOUNT_TAMPERED" for i in report.issues))

    def test_inject_ferry_in_non_ferry_trip_fails(self):
        req = create_trip_request("Rajasthan", days=4)
        doc = build_proposal_document_from_trip(req)

        # Tamper: inject ferry bullet in Rajasthan
        day_1 = doc.get_section("sec_day_1")
        day_1.content.schedule_bullets[0].text.value = "Board Makruzz private ferry transfer across the desert."

        report = validate_proposal_document(doc)
        self.assertFalse(report.is_valid)
        self.assertTrue(any(i.code == "DEST_INVALID_FERRY_USAGE" for i in report.issues))


class TestAndamanGoldenRegression(unittest.TestCase):
    """Ensures canonical Andaman behavior is 100% preserved."""

    def test_andaman_canonical_entities_preserved(self):
        req = create_trip_request(
            destination="Andaman",
            days=5,
            hotel="Symphony Palms Beach Resort",
            customer_name="Priya Patel",
        )
        sample_andaman_itinerary = """
        Day 1: Arrival in Port Blair & Cellular Jail
        Witness the heroic history of India at Cellular Jail National Memorial.
        Day 2: Havelock Island Transfer & Radhanagar Beach
        Board private catamaran ferry to Swaraj Dweep (Havelock) and visit Radhanagar Beach.
        Day 3: Elephant Beach & Marine Life
        Enjoy complimentary snorkeling and glass bottom boat ride.
        Day 4: Shaheed Dweep (Neil) & Natural Rock Bridge
        Explore Bharatpur and Laxmanpur beaches.
        Day 5: Port Blair Departure
        Transfer to Veer Savarkar International Airport for departure.
        """
        doc = build_proposal_document_from_trip(req, sample_andaman_itinerary)

        self.assertTrue(doc.destination_context.is_andaman)
        self.assertTrue(doc.destination_context.has_verified_ferry_movement)
        self.assertIn("Veer Savarkar", str(doc.destination_context.entry_hub))
        self.assertIn("Andaman", doc.agency_context.legal_name)

        report = validate_proposal_document(doc)
        self.assertTrue(report.is_valid, f"Andaman validation failed: {[i.message for i in report.issues]}")


if __name__ == "__main__":
    unittest.main()
