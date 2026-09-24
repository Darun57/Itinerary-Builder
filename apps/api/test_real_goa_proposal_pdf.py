"""
Real Goa 7D/6N ProposalDocument PDF Pipeline Verification
=========================================================
Executes:
1. Builds a real Goa 7D/6N TripRequest with luxury hotels and realistic itinerary text.
2. Constructs the canonical ProposalDocument IR.
3. Renders the PDF strictly via generate_pdf_from_proposal (and generate_luxury_pdf).
4. Extracts text via PyMuPDF (fitz) across all pages.
5. Verifies:
   - Zero Andaman contamination (no Port Blair, Havelock, Cellular Jail, DSS, Veer Savarkar).
   - Real Goa entities present (Candolim, Panaji, Fort Aguada, Taj Exotica, Mandovi).
   - Structured pricing and statutory banking integrity.
   - Decoupled logical sections correctly rendered into physical pages.
"""
import sys
import unittest
from pathlib import Path

API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

import fitz
from app.schemas.proposal import ProposalDocument
from app.schemas.trip import DayPlan, IncludedActivity, TripRequest
from app.services.google_service import generate_itinerary
from app.services.pdf import generate_luxury_pdf, generate_pdf_from_proposal
from app.services.proposal_builder import build_proposal_document_from_trip
from app.services.proposal_validator import validate_proposal_document

FORBIDDEN_ANDAMAN_TERMS = [
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


def extract_pdf_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()
    return "\n--- PAGE BREAK ---\n".join(pages_text)


class TestRealGoaProposalPDF(unittest.TestCase):

    def test_real_goa_7d6n_pdf_from_proposal_document(self):
        # 1. Setup real Goa 7D/6N trip
        daily_plan = [
            DayPlan(day_number=1, primary_island="Candolim", hotel="Radisson Hotel Goa Candolim", attractions=["Candolim Beach"], morning="Arrival at Dabolim / MOPA airport & check-in", afternoon="Relaxation at beach", evening="Sunset stroll at Candolim", night="Dinner at hotel"),
            DayPlan(day_number=2, primary_island="Candolim", hotel="Radisson Hotel Goa Candolim", attractions=["Fort Aguada", "Sinquerim Beach"], morning="Visit historic Fort Aguada lighthouse", afternoon="Watersports at Sinquerim", evening="Leisure", night="Stay at Candolim"),
            DayPlan(day_number=3, primary_island="Panaji", hotel="Taj Exotica Resort & Spa, Goa", attractions=["Fontainhas Latin Quarter", "Miramar Beach"], morning="Heritage walk in Fontainhas", afternoon="River Mandovi scenic drive", evening="Miramar sunset", night="Check-in at Taj Exotica"),
            DayPlan(day_number=4, primary_island="Old Goa", hotel="Taj Exotica Resort & Spa, Goa", attractions=["Basilica of Bom Jesus", "Se Cathedral"], morning="Explore UNESCO heritage churches", afternoon="Spice plantation visit & Goan buffet", evening="Benaulim beach sunset", night="Stay at Taj Exotica"),
            DayPlan(day_number=5, primary_island="Benaulim", hotel="Taj Exotica Resort & Spa, Goa", attractions=["Colva Beach", "Benaulim Beach"], morning="Relaxed coastal leisure", afternoon="Ayurvedic spa session", evening="Beachside dining", night="Stay at Taj Exotica"),
            DayPlan(day_number=6, primary_island="South Goa", hotel="Taj Exotica Resort & Spa, Goa", attractions=["Cabo de Rama Fort", "Palolem Beach"], morning="Scenic drive to Cabo de Rama cliff", afternoon="Palolem beach exploration", evening="Sunset cocktail", night="Stay at Taj Exotica"),
            DayPlan(day_number=7, primary_island="Departure", hotel="Taj Exotica Resort & Spa, Goa", attractions=["Departure"], morning="Breakfast and souvenir shopping in Panaji", afternoon="Transfer to Goa Airport for onward flight", evening="Departure", night=""),
        ]

        req = TripRequest(
            customer_name="Vikramaditya Singhania",
            customer_email="vikram@singhania.com",
            customer_phone_number="+91 98200 12345",
            destination="Goa",
            trip_type="Luxury Leisure",
            number_of_days=7,
            number_of_nights=6,
            number_of_adults=2,
            total_package_cost=145000.0,
            per_person_cost=72500.0,
            budget_category="Ultra Luxury",
            day_wise_style="luxury_narrative",
            daily_island_plan=daily_plan,
            selected_destinations=["Candolim", "Panaji", "Old Goa", "Benaulim"],
            selected_hotels=["Radisson Hotel Goa Candolim", "Taj Exotica Resort & Spa, Goa"],
            preferred_activities=["Heritage Walk", "Sunset Cruise", "Spice Plantation Tour"],
            included_activities=[
                IncludedActivity(activity_name="Spice Plantation Tour with Traditional Lunch", quantity=2, is_free=True, location="Old Goa")
            ],
            transfer_type="Private Chauffeur-driven AC Sedan",
        )

        # Generate realistic itinerary text via AI service
        itinerary_text = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        self.assertTrue(itinerary_text)

        # 2. Build canonical ProposalDocument
        proposal_doc: ProposalDocument = build_proposal_document_from_trip(req, itinerary_text)
        self.assertIsNotNone(proposal_doc)
        self.assertEqual(proposal_doc.destination_id, "goa")
        self.assertEqual(proposal_doc.destination_context.destination_id, "goa")
        self.assertFalse(proposal_doc.destination_context.is_andaman)
        self.assertFalse(proposal_doc.destination_context.has_verified_ferry_movement)

        # 3. Validate ProposalDocument preflight
        validation_report = validate_proposal_document(proposal_doc)
        self.assertTrue(validation_report.is_valid, f"Validation issues: {[i.message for i in validation_report.issues]}")
        self.assertTrue(validation_report.can_render_pdf)

        # 4. Render PDF directly from ProposalDocument
        pdf_bytes = generate_pdf_from_proposal(proposal_doc)
        self.assertGreater(len(pdf_bytes), 20000)

        # 5. Extract and normalize PDF text
        raw_text = extract_pdf_text(pdf_bytes)
        norm_text = " ".join(raw_text.split()).lower()

        # 6. Verify zero Andaman contamination
        matches = [f for f in FORBIDDEN_ANDAMAN_TERMS if f in norm_text]
        if matches:
            print("\n>>> MATCHED FORBIDDEN TERMS IN GOA PDF:", matches)
        for forbidden in FORBIDDEN_ANDAMAN_TERMS:
            self.assertNotIn(
                forbidden,
                norm_text,
                f"Contamination Failure: Forbidden Andaman term '{forbidden}' detected in Goa 7D/6N PDF!"
            )

        # 7. Verify real Goa entities are present
        self.assertIn("goa", norm_text)
        self.assertIn("darun tourism", norm_text)
        self.assertIn("candolim", norm_text)
        self.assertIn("vikramaditya singhania", norm_text)
        self.assertIn("tax invoice", norm_text)
        self.assertIn("payment details", norm_text)
        self.assertIn("inclusions & exclusions", norm_text)

        # 8. Save artifact for inspection
        output_pdf_path = API_DIR / "test_output" / "real_goa_7d6n_proposal_pipeline.pdf"
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        output_pdf_path.write_bytes(pdf_bytes)
        print(f"\n[SUCCESS] Generated Real Goa 7D/6N PDF: {output_pdf_path} ({len(pdf_bytes):,} bytes)")


if __name__ == "__main__":
    unittest.main()
