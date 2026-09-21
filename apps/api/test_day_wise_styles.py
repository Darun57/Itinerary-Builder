"""
Validation script for Day-wise Itinerary Writing Styles.
Tests:
1. Andaman itinerary — Luxury Narrative
2. Andaman itinerary — Simple Itinerary
3. Another destination — Luxury Narrative
4. Another destination — Simple Itinerary
5. Legacy / default request (without day_wise_style explicitly provided)
"""
import json
import sys
from pathlib import Path

# Add apps/api to path
api_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(api_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.schemas.trip import TripRequest, DayPlan
from app.services.itinerary_normalizer import normalize_itinerary_payload
from app.services.pdf.builder import generate_luxury_pdf
from app.services.pdf.day_parser import split_itinerary_into_days


def build_andaman_trip_request(style: str = None) -> TripRequest:
    kwargs = {
        "customer_name": "Karan Sharma",
        "customer_email": "karan@example.com",
        "customer_phone_number": "+91 9876543210",
        "customer_nationality": "Indian",
        "destination": "Andaman Islands",
        "number_of_days": 4,
        "number_of_nights": 3,
        "arrival_date": "2026-11-20",
        "departure_date": "2026-11-23",
        "trip_type": "Family Vacation",
        "budget_category": "Luxury",
        "number_of_adults": 2,
        "number_of_children": 1,
        "number_of_infants": 0,
        "number_of_senior_citizens": 0,
        "meal_plan": "CP (Breakfast)",
        "transfer_type": "Private AC Cab",
        "selected_hotels": ["Sinclairs Bayview", "Aquyas Hotel & Resort"],
        "selected_destinations": ["Port Blair", "Havelock Island", "Neil Island"],
        "preferred_activities": ["Scuba Diving", "Sightseeing"],
        "daily_island_plan": [
            DayPlan(
                day_number=1,
                primary_island="Port Blair",
                attractions=["Corbyn's Cove Beach", "Cellular Jail & Light and Sound Show"],
                activities=["Sightseeing"],
                hotel="Sinclairs Bayview",
                ferry="",
                transfer_type="Private AC Cab",
            ),
            DayPlan(
                day_number=2,
                primary_island="Swaraj Dweep (Havelock)",
                attractions=["Radhanagar Beach", "Kalapathar Beach"],
                activities=["Sunset Visit"],
                hotel="Aquyas Hotel & Resort",
                ferry="Makruzz Luxury Ferry",
                ferry_timing="08:00 AM",
                transfer_type="Private AC Cab",
            ),
            DayPlan(
                day_number=3,
                primary_island="Shaheed Dweep (Neil)",
                attractions=["Bharatpur Beach", "Natural Rock Arch", "Laxmanpur Beach"],
                activities=["Beach Exploration"],
                hotel="Aquyas Hotel & Resort",
                ferry="Green Ocean Ferry",
                ferry_timing="10:00 AM",
                transfer_type="Private AC Cab",
            ),
            DayPlan(
                day_number=4,
                primary_island="Departure",
                attractions=["Departure"],
                activities=["Private Airport Transfer"],
                hotel="",
                ferry="",
                transfer_type="Private AC Cab",
            ),
        ],
    }
    if style is not None:
        kwargs["day_wise_style"] = style
    return TripRequest(**kwargs)


def build_goa_trip_request(style: str = None) -> TripRequest:
    kwargs = {
        "customer_name": "Priya Mehta",
        "customer_email": "priya@example.com",
        "customer_phone_number": "+91 9123456780",
        "customer_nationality": "Indian",
        "destination": "Goa",
        "number_of_days": 3,
        "number_of_nights": 2,
        "arrival_date": "2026-12-05",
        "departure_date": "2026-12-07",
        "trip_type": "Couples Getaway",
        "budget_category": "Luxury",
        "number_of_adults": 2,
        "number_of_children": 0,
        "number_of_infants": 0,
        "number_of_senior_citizens": 0,
        "meal_plan": "MAP (Breakfast & Dinner)",
        "transfer_type": "Private Chauffeur AC Sedan",
        "selected_hotels": ["Novotel Goa Resort & Spa"],
        "selected_destinations": ["Panaji", "North Goa"],
        "daily_island_plan": [
            DayPlan(
                day_number=1,
                primary_island="Panaji",
                attractions=["Fontainhas Latin Quarter", "Mandovi Riverfront"],
                activities=["Heritage Walk"],
                hotel="Novotel Goa Resort & Spa",
                transfer_type="Private Chauffeur AC Sedan",
            ),
            DayPlan(
                day_number=2,
                primary_island="North Goa",
                attractions=["Calangute Beach", "Anjuna Flea Market"],
                activities=["Beach Tour"],
                hotel="Novotel Goa Resort & Spa",
                transfer_type="Private Chauffeur AC Sedan",
            ),
            DayPlan(
                day_number=3,
                primary_island="Departure",
                attractions=["Departure"],
                activities=["Airport Transfer"],
                hotel="",
                transfer_type="Private Chauffeur AC Sedan",
            ),
        ],
    }
    if style is not None:
        kwargs["day_wise_style"] = style
    return TripRequest(**kwargs)


def generate_mock_raw_json(request: TripRequest) -> str:
    """Simulates Gemini generating raw day objects based on the request's daily_island_plan."""
    days = []
    for dp in request.daily_island_plan:
        days.append({
            "day_number": dp.day_number,
            "primary_island": dp.primary_island,
            "attractions": dp.attractions,
            "activities": dp.activities,
            "hotel": dp.hotel,
        })
    return json.dumps({"days": days})


def run_tests():
    print("==================================================")
    print("RUNNING DAY-WISE ITINERARY STYLE VALIDATION SUITE")
    print("==================================================")

    # -------------------------------------------------------------
    # Test 1: Andaman — Luxury Narrative
    # -------------------------------------------------------------
    print("\n--- Test 1: Andaman — Luxury Narrative ---")
    req_andaman_lux = build_andaman_trip_request("luxury_narrative")
    raw_json_1 = generate_mock_raw_json(req_andaman_lux)
    norm_json_1 = normalize_itinerary_payload(raw_json_1, req_andaman_lux)
    parsed_1 = json.loads(norm_json_1)["days"]
    
    assert req_andaman_lux.day_wise_style == "luxury_narrative"
    assert len(parsed_1) == 4
    # Check Day 2 has luxury narrative sections
    day2_lux = parsed_1[1]
    assert day2_lux["day_wise_style"] == "luxury_narrative"
    assert "visiting_places" in day2_lux and len(day2_lux["visiting_places"]) > 20
    assert "destination_story" in day2_lux and len(day2_lux["destination_story"]) > 20
    assert day2_lux["todays_journey"].startswith("For the places highlighted above, ")
    assert "Aquyas Hotel & Resort" in day2_lux["hotel_experience"]
    print("[PASS] Day 2 Luxury Narrative text verified (Visiting places, Destination story, Today's Journey, Hotel Experience).")

    # Verify PDF compilation
    pdf_bytes_1 = generate_luxury_pdf(req_andaman_lux, norm_json_1)
    assert len(pdf_bytes_1) > 10000
    print(f"[PASS] Andaman Luxury Narrative PDF generated successfully ({len(pdf_bytes_1)} bytes).")

    # -------------------------------------------------------------
    # Test 2: Andaman — Simple Itinerary
    # -------------------------------------------------------------
    print("\n--- Test 2: Andaman -- Simple Itinerary ---")
    req_andaman_simple = build_andaman_trip_request("simple_itinerary")
    raw_json_2 = generate_mock_raw_json(req_andaman_simple)
    norm_json_2 = normalize_itinerary_payload(raw_json_2, req_andaman_simple)
    parsed_2 = json.loads(norm_json_2)["days"]

    assert req_andaman_simple.day_wise_style == "simple_itinerary"
    assert len(parsed_2) == 4
    day2_simple = parsed_2[1]
    assert day2_simple["day_wise_style"] == "simple_itinerary"
    assert "operational_bullets" in day2_simple
    bullets = day2_simple["operational_bullets"]
    
    # Verify bullet contents
    assert any("ferry" in b.lower() and "makruzz" in b.lower() for b in bullets), "Ferry not found in bullets"
    assert any("radhanagar" in b.lower() for b in bullets), "Radhanagar not found in bullets"
    assert any("kalapathar" in b.lower() for b in bullets), "Kalapathar not found in bullets"
    assert any("overnight stay" in b.lower() for b in bullets), "Overnight stay bullet missing"
    assert day2_simple["destination_story"] == "", "Destination story should be empty in simple style"
    print("[PASS] Day 2 Simple Itinerary operational bullets verified:")
    for b in bullets:
        print(f"   * {b}")

    # Verify split_itinerary_into_days parser for Simple Itinerary
    sections_2 = split_itinerary_into_days(norm_json_2)
    assert len(sections_2) == 4
    items_day_2 = sections_2[1]["items"]
    bullet_items = [it for it in items_day_2 if it.get("is_bullets")]
    assert len(bullet_items) > 0, "No bullet item found in parsed PDF section"
    print("[PASS] PDF day_parser properly structured TODAYS SCHEDULE bullets.")

    # Verify PDF compilation
    pdf_bytes_2 = generate_luxury_pdf(req_andaman_simple, norm_json_2)
    assert len(pdf_bytes_2) > 10000
    print(f"[PASS] Andaman Simple Itinerary PDF generated successfully ({len(pdf_bytes_2)} bytes).")

    # -------------------------------------------------------------
    # Test 3: Destination Goa — Luxury Narrative
    # -------------------------------------------------------------
    print("\n--- Test 3: Goa -- Luxury Narrative ---")
    req_goa_lux = build_goa_trip_request("luxury_narrative")
    raw_json_3 = generate_mock_raw_json(req_goa_lux)
    norm_json_3 = normalize_itinerary_payload(raw_json_3, req_goa_lux)
    pdf_bytes_3 = generate_luxury_pdf(req_goa_lux, norm_json_3)
    assert len(pdf_bytes_3) > 10000
    print(f"[PASS] Goa Luxury Narrative PDF generated successfully ({len(pdf_bytes_3)} bytes).")

    # -------------------------------------------------------------
    # Test 4: Destination Goa — Simple Itinerary
    # -------------------------------------------------------------
    print("\n--- Test 4: Goa -- Simple Itinerary ---")
    req_goa_simple = build_goa_trip_request("simple_itinerary")
    raw_json_4 = generate_mock_raw_json(req_goa_simple)
    norm_json_4 = normalize_itinerary_payload(raw_json_4, req_goa_simple)
    parsed_4 = json.loads(norm_json_4)["days"]
    day1_goa = parsed_4[0]
    assert day1_goa["day_wise_style"] == "simple_itinerary"
    assert "operational_bullets" in day1_goa
    assert any("fontainhas" in b.lower() for b in day1_goa["operational_bullets"])
    pdf_bytes_4 = generate_luxury_pdf(req_goa_simple, norm_json_4)
    assert len(pdf_bytes_4) > 10000
    print(f"[PASS] Goa Simple Itinerary PDF generated successfully ({len(pdf_bytes_4)} bytes).")

    # -------------------------------------------------------------
    # Test 5: Backward Compatibility (No style supplied)
    # -------------------------------------------------------------
    print("\n--- Test 5: Backward Compatibility (Default / Unspecified Style) ---")
    req_legacy = build_andaman_trip_request(style=None)
    assert req_legacy.day_wise_style == "luxury_narrative", "Default must be luxury_narrative"
    raw_json_5 = generate_mock_raw_json(req_legacy)
    norm_json_5 = normalize_itinerary_payload(raw_json_5, req_legacy)
    parsed_5 = json.loads(norm_json_5)["days"]
    assert parsed_5[1]["day_wise_style"] == "luxury_narrative"
    assert "visiting_places" in parsed_5[1]
    pdf_bytes_5 = generate_luxury_pdf(req_legacy, norm_json_5)
    assert len(pdf_bytes_5) > 10000
    print(f"[PASS] Unspecified style safely defaults to luxury_narrative ({len(pdf_bytes_5)} bytes).")

    # Save sample test PDFs for visual inspection
    out_dir = api_dir / "test_output"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "Andaman_Luxury_Narrative.pdf").write_bytes(pdf_bytes_1)
    (out_dir / "Andaman_Simple_Itinerary.pdf").write_bytes(pdf_bytes_2)
    (out_dir / "Goa_Luxury_Narrative.pdf").write_bytes(pdf_bytes_3)
    (out_dir / "Goa_Simple_Itinerary.pdf").write_bytes(pdf_bytes_4)
    print(f"\nAll test PDFs saved to: {out_dir}")

    print("\n==================================================")
    print("ALL 5 VALIDATION TESTS PASSED PERFECTLY!")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
