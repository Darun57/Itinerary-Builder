"""
Automated Destination Isolation Pipeline Test Suite
====================================================
End-to-end production verification for destination-aware itinerary and PDF generation.

Coverage:
- Gate 1: Goa E2E PDF Generation (Simple Itinerary style) — fitz text extraction & zero-leak assertions.
- Gate 2: Goa E2E PDF Generation (Luxury Narrative style) — fitz text extraction & zero-leak assertions.
- Gate 3: Hotel provenance validation (Goa hotels resolve to Goa locations, never Andaman).
- Gate 4: Entry hub non-invention (Never invent "{destination} Airport").
- Gate 5: Ferry clause data-driven gating (Absence of ferry clauses when no verified ferry movements).
- Gate 6: AgencyContext & legal entity scoping (Darun Tourism vs Andaman Darun).
- Gate 7: Rajasthan E2E PDF Generation — fitz extraction, zero Andaman & zero Goa leaks.
- Gate 8: Kashmir E2E PDF Generation — fitz extraction, zero Andaman & zero Goa leaks.
- Gate 9: Andaman Golden Reference Regression — Canonical Andaman PDF contains all required entities.
"""
import io
import json
import os
import sys
import unittest
from pathlib import Path

# Ensure api root is on path
API_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(API_DIR))

import fitz  # PyMuPDF
from app.schemas.trip import TripRequest
from app.services.google_service import generate_itinerary
from app.services.pdf.builder import generate_luxury_pdf
from app.services.destination_registry import (
    get_destination_context,
    load_hotels as reg_load_hotels,
    load_movements,
)
from app.services.pdf.sections.hotels import _lookup_hotel_metadata


FORBIDDEN_IN_GOA = [
    "port blair",
    "havelock",
    "swaraj dweep",
    "shaheed dweep",
    "neil island",
    "cellular jail",
    "veer savarkar",
    "dss",
    "makruzz",
    "nautika",
    "green ocean",
    "andaman islands",
    "andaman darun",
    "andamandaruntour",
    "port management board",
    "bay of bengal",
    "island journey",
    "smooth island connectivity",
    "island holiday",
    "island getaway",
]

REQUIRED_IN_ANDAMAN = [
    "port blair",
    "veer savarkar",
    "andaman islands darun tours and travels",
]


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract all text from PDF bytes across all pages."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()
    return "\n--- PAGE BREAK ---\n".join(pages_text)


def normalize_whitespace(text: str) -> str:
    import re
    return re.sub(r"\s+", " ", text).strip().lower()


class TestDestinationIsolationPipeline(unittest.TestCase):

    def test_g1_goa_simple_pdf_e2e(self):
        """Gate 1: Goa 7D/6N in Simple Itinerary style generates clean PDF with zero Andaman leaks."""
        req = TripRequest(
            customer_name="Rohan Verma",
            customer_email="rohan.verma@example.com",
            customer_phone="+91 98765 43210",
            destination="Goa",
            trip_type="Honeymoon",
            number_of_days=7,
            number_of_nights=6,
            day_wise_style="simple_itinerary",
            selected_hotels=["Radisson Hotel Goa Candolim", "Taj Exotica Resort & Spa, Goa"],
            selected_destinations=["Candolim", "Panaji", "Old Goa", "Benaulim"],
            preferred_activities=["Beachside Relaxation", "Sunset Cruise", "Heritage Walk"],
            transfer_type="Private Cab",
            budget_category="Luxury",
            meal_plan="Daily Breakfast",
        )
        # Generate normalized itinerary JSON
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(raw_result, "generate_itinerary returned empty result")

        # Generate real PDF bytes
        pdf_bytes = generate_luxury_pdf(req, raw_result)
        self.assertGreater(len(pdf_bytes), 10000, "Generated PDF bytes too small")

        # Extract all text streams using fitz
        full_pdf_text = extract_pdf_text(pdf_bytes)
        norm_text = normalize_whitespace(full_pdf_text)

        # Strict scan for every forbidden entity
        for forbidden in FORBIDDEN_IN_GOA:
            self.assertNotIn(
                forbidden,
                norm_text,
                f"[Gate 1: Goa Simple PDF] Forbidden entity '{forbidden}' detected in PDF text!"
            )

        # Positive assertions
        self.assertIn("darun tourism", norm_text)
        self.assertIn("goa", norm_text)
        self.assertIn("rohan verma", norm_text)
        self.assertIn("invoice", norm_text)

    def test_g2_goa_luxury_pdf_e2e(self):
        """Gate 2: Goa 7D/6N in Luxury Narrative style generates clean PDF with zero Andaman leaks."""
        req = TripRequest(
            customer_name="Aarav Sharma",
            customer_email="aarav.sharma@example.com",
            customer_phone="+91 91234 56789",
            destination="Goa",
            trip_type="Couples Getaway",
            number_of_days=7,
            number_of_nights=6,
            day_wise_style="luxury_narrative",
            selected_hotels=["Alila Diwa Goa", "Grand Hyatt Goa"],
            selected_destinations=["Majorda", "Bambolim", "Panaji"],
            preferred_activities=["Spa Experience", "Gourmet Dining"],
            transfer_type="Private Cab",
            budget_category="Ultra Luxury",
            meal_plan="Breakfast and Dinner",
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(raw_result)

        pdf_bytes = generate_luxury_pdf(req, raw_result)
        self.assertGreater(len(pdf_bytes), 10000)

        full_pdf_text = extract_pdf_text(pdf_bytes)
        norm_text = normalize_whitespace(full_pdf_text)

        for forbidden in FORBIDDEN_IN_GOA:
            self.assertNotIn(
                forbidden,
                norm_text,
                f"[Gate 2: Goa Luxury PDF] Forbidden entity '{forbidden}' detected in PDF text!"
            )

    def test_g3_hotel_provenance_and_resolution(self):
        """Gate 3: Goa hotels resolve strictly to Goa locations, never Port Blair or Havelock."""
        goa_hotels_to_test = [
            ("Radisson Hotel Goa Candolim", "Candolim"),
            ("Taj Exotica Resort & Spa, Goa", "Benaulim"),
            ("Hotel Fidalgo", "Panaji"),
            ("Panjim Inn", "Fontainhas"),
            ("Alila Diwa Goa", "Majorda"),
        ]
        for hotel_name, expected_loc in goa_hotels_to_test:
            meta = _lookup_hotel_metadata(hotel_name, None, "Goa")
            loc = meta.get("location", "")
            self.assertEqual(
                loc.lower(),
                expected_loc.lower(),
                f"Hotel '{hotel_name}' resolved to location '{loc}', expected '{expected_loc}'"
            )
            self.assertNotIn("port blair", loc.lower())
            self.assertNotIn("havelock", loc.lower())
            self.assertNotIn("swaraj dweep", loc.lower())

    def test_g4_entry_hub_non_invention(self):
        """Gate 4: Entry hub is never fabricated as '{destination} Airport'."""
        for dest in ["Goa", "Rajasthan", "Kashmir", "Himachal Pradesh", "Kerala"]:
            ctx = get_destination_context(dest)
            if ctx.entry_hub is not None:
                self.assertNotIn(
                    f"{dest.lower()} airport",
                    ctx.entry_hub.lower(),
                    f"Fabricated airport name found for {dest}: {ctx.entry_hub}"
                )

    def test_g5_ferry_clause_data_driven_gating(self):
        """Gate 5: Ferry clauses omitted when trip has no verified ferry movements."""
        ctx_goa = get_destination_context("Goa")
        self.assertFalse(
            ctx_goa.has_verified_ferry_movement,
            "Goa trip should NOT have verified ferry movements"
        )
        ctx_andaman = get_destination_context("Andaman Islands")
        self.assertTrue(
            ctx_andaman.has_verified_ferry_movement,
            "Andaman trip must have verified ferry movements"
        )

    def test_g6_agency_context_and_invoice_isolation(self):
        """Gate 6: AgencyContext vs DestinationContext separation."""
        ctx_goa = get_destination_context("Goa")
        self.assertEqual(ctx_goa.agency_legal_name, "Darun Tourism")
        self.assertEqual(ctx_goa.agency_location, "India")
        self.assertEqual(ctx_goa.agency_email, "info@daruntourism.in")
        self.assertEqual(ctx_goa.agency_website, "www.daruntourism.in")

        ctx_andaman = get_destination_context("Andaman Islands")
        self.assertEqual(ctx_andaman.agency_legal_name, "Andaman Islands Darun Tours and Travels")
        self.assertEqual(ctx_andaman.agency_location, "Andaman Islands, India")

    def test_g7_rajasthan_pdf_e2e(self):
        """Gate 7: Rajasthan PDF generation has zero Andaman and zero Goa entities."""
        req = TripRequest(
            customer_name="Vikramaditya Rathore",
            customer_email="vikram@example.com",
            customer_phone="+91 99887 76655",
            destination="Rajasthan",
            trip_type="Heritage Tour",
            number_of_days=6,
            number_of_nights=5,
            day_wise_style="simple_itinerary",
            selected_destinations=["Jaipur", "Udaipur", "Jodhpur"],
            preferred_activities=["Fort Exploration", "Palace Tour"],
            transfer_type="Private Cab",
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(raw_result)

        pdf_bytes = generate_luxury_pdf(req, raw_result)
        self.assertGreater(len(pdf_bytes), 10000)

        full_pdf_text = extract_pdf_text(pdf_bytes)
        norm_text = normalize_whitespace(full_pdf_text)

        # Zero Andaman entities
        for forbidden in FORBIDDEN_IN_GOA:
            self.assertNotIn(
                forbidden,
                norm_text,
                f"[Gate 7: Rajasthan PDF] Andaman entity '{forbidden}' detected in Rajasthan PDF!"
            )
        # Zero Goa-only entities
        for goa_entity in ["candolim", "benaulim", "calangute", "baga beach"]:
            self.assertNotIn(
                goa_entity,
                norm_text,
                f"[Gate 7: Rajasthan PDF] Goa entity '{goa_entity}' detected in Rajasthan PDF!"
            )

    def test_g8_kashmir_pdf_e2e(self):
        """Gate 8: Kashmir PDF generation has zero Andaman and zero Goa entities."""
        req = TripRequest(
            customer_name="Pooja Mehta",
            customer_email="pooja@example.com",
            customer_phone="+91 94567 12345",
            destination="Kashmir",
            trip_type="Family Vacation",
            number_of_days=5,
            number_of_nights=4,
            day_wise_style="luxury_narrative",
            selected_destinations=["Srinagar", "Gulmarg", "Pahalgam"],
            preferred_activities=["Shikara Ride", "Gondola Ride"],
            transfer_type="Private Cab",
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(raw_result)

        pdf_bytes = generate_luxury_pdf(req, raw_result)
        self.assertGreater(len(pdf_bytes), 10000)

        full_pdf_text = extract_pdf_text(pdf_bytes)
        norm_text = normalize_whitespace(full_pdf_text)

        # Zero Andaman entities
        for forbidden in FORBIDDEN_IN_GOA:
            self.assertNotIn(
                forbidden,
                norm_text,
                f"[Gate 8: Kashmir PDF] Andaman entity '{forbidden}' detected in Kashmir PDF!"
            )
        # Zero Goa-only entities
        for goa_entity in ["candolim", "benaulim", "calangute", "baga beach"]:
            self.assertNotIn(
                goa_entity,
                norm_text,
                f"[Gate 8: Kashmir PDF] Goa entity '{goa_entity}' detected in Kashmir PDF!"
            )

    def test_g9_andaman_golden_regression_e2e(self):
        """Gate 9: Andaman Golden Reference Regression — All canonical entities present."""
        req = TripRequest(
            customer_name="Ananya Roy",
            customer_email="ananya.roy@example.com",
            customer_phone="+91 93344 55667",
            destination="Andaman Islands",
            trip_type="Honeymoon",
            number_of_days=7,
            number_of_nights=6,
            day_wise_style="simple_itinerary",
            selected_hotels=["SeaShell Port Blair", "Symphony Palms"],
            selected_destinations=["Port Blair", "Havelock", "Neil Island"],
            preferred_activities=["Snorkelling", "Scuba Diving"],
            preferred_ferries=["Makruzz"],
            transfer_type="Private Cab",
            budget_category="Luxury",
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(raw_result)

        pdf_bytes = generate_luxury_pdf(req, raw_result)
        self.assertGreater(len(pdf_bytes), 10000)

        full_pdf_text = extract_pdf_text(pdf_bytes)
        norm_text = normalize_whitespace(full_pdf_text)

        # Required canonical Andaman entities MUST be present
        for required in REQUIRED_IN_ANDAMAN:
            self.assertIn(
                required,
                norm_text,
                f"[Gate 9: Andaman Regression] Required canonical entity '{required}' MISSING from Andaman PDF!"
            )

        # Island journey language must be present
        self.assertIn("island journey", norm_text)
        self.assertIn("smooth island connectivity", norm_text)

        # Ferry policies must be rendered
        self.assertIn("carrier & ferry policies", norm_text)
        self.assertIn("makruzz", norm_text)
        self.assertIn("port management board directives", norm_text)


if __name__ == "__main__":
    unittest.main()
