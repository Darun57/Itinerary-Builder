"""
Unit tests for Narrative Intelligence Validator, Observability Logger, and Raw Archiving.
"""
import json
from app.schemas.trip import TripRequest
from app.services.narrative_validator import (
    validate_schema,
    evaluate_quality_score,
    validate_consistency,
    validate_full_itinerary,
)


@pytest.fixture
def sample_request():
    return TripRequest(
        customer_name="Aarav Sharma",
        destination="Andaman and Nicobar Islands",
        number_of_days=2,
        number_of_nights=1,
        arrival_date="2026-08-01",
        departure_date="2026-08-02",
        trip_type="Honeymoon",
        selected_hotels=["Taj Exotica Resort & Spa"],
    )


@pytest.fixture
def high_quality_json():
    return json.dumps({
        "days": [
            {
                "day_number": 1,
                "title": "Day 1: Arrival in Port Blair",
                "subtitle": "Warm Tropical Welcome",
                "primary_island": "Port Blair",
                "travel_movement": "Airport Private Driver Transfer",
                "destination_story": "The morning opens with a warm tropical ocean breeze as you touch down at Veer Savarkar International Airport in Port Blair. Your private driver greets you with fresh garlands before heading through lush palm-lined coastal roads to your resort.",
                "todays_journey": "Private luxury vehicle transfer from Airport to Taj Exotica Resort & Spa takes approximately 25 minutes. Smooth coastal drive with scenic harbor views.",
                "curated_experience": "Afternoon sunset stroll along Corbyn's Cove beach followed by private photography session during golden hour over the Bay of Bengal.",
                "hotel_experience": "Check into Taj Exotica Resort & Spa for a luxurious villa experience with private plunge pool and personalized concierge welcome amenities.",
                "expert_insider_notes": "Carry crisp INR currency notes as local island shops near cellular jail have limited card terminal network connectivity.",
                "next_day_transition": "Tomorrow morning features an early private luxury Makruzz catamaran ferry crossing across the azure sea to Havelock Island.",
                "hotel": "Taj Exotica Resort & Spa",
                "activities": ["Corbyn's Cove Beach Stroll"],
                "attractions": ["Cellular Jail"],
                "image_keyword": "andaman_beach"
            },
            {
                "day_number": 2,
                "title": "Day 2: Departure from Port Blair",
                "subtitle": "Farewell to Paradise",
                "primary_island": "Port Blair",
                "travel_movement": "Private Driver Airport Transfer",
                "destination_story": "Your final morning in Port Blair offers a serene breakfast overlooking the turquoise bay. Take time for last-minute souvenir shopping before your departure.",
                "todays_journey": "Ferry/Transfer: via Private Transfer at 10:00 AM to Veer Savarkar International Airport for return flight.",
                "curated_experience": "Curated morning shopping tour for handcrafted pearl souvenirs and local spices before final airport check-in.",
                "hotel_experience": "Enjoy a leisurely late check-out at Taj Exotica Resort & Spa with complimentary breakfast included.",
                "expert_insider_notes": "Arrive at airport 2 hours prior to scheduled departure time due to security queues.",
                "next_day_transition": "Safe travels on your return flight carrying lifelong memories of your luxury Andaman getaway.",
                "hotel": "Taj Exotica Resort & Spa",
                "activities": ["Souvenir Shopping"],
                "attractions": ["Local Market"],
                "image_keyword": "andaman_sunset"
            }
        ]
    })


def test_schema_validator_success():
    valid_day = {
        "destination_story": "Valid story content for testing",
        "todays_journey": "Valid journey content for testing",
        "curated_experience": "Valid curated experience content",
        "hotel_experience": "Valid hotel experience content",
        "expert_insider_notes": "Valid insider notes content",
        "next_day_transition": "Valid transition content for testing",
    }
    ok, errors = validate_schema(valid_day)
    assert ok is True
    assert len(errors) == 0


def test_schema_validator_missing_field():
    incomplete_day = {
        "destination_story": "Valid story content for testing",
    }
    ok, errors = validate_schema(incomplete_day)
    assert ok is False
    assert any("todays_journey" in e for e in errors)


def test_quality_scoring_high(sample_request, high_quality_json):
    result = validate_full_itinerary(high_quality_json, sample_request)
    assert result["valid"] is True
    assert result["overall_score"] >= 70.0
    assert len(result["failed_rules"]) == 0


def test_consistency_validator_day1_departure_error(sample_request):
    invalid_days = [
        {
            "day_number": 1,
            "title": "Day 1: Departure flight home",
            "primary_island": "Port Blair",
            "destination_story": "Heading to return flight.",
            "todays_journey": "Transfer to airport for return flight."
        },
        {
            "day_number": 2,
            "title": "Day 2: Departure",
            "primary_island": "Port Blair",
            "destination_story": "Final day.",
            "todays_journey": "Departure."
        }
    ]
    ok, errors = validate_consistency(invalid_days, sample_request)
    assert ok is False
    assert any("Day 1 contains departure" in e for e in errors)


if __name__ == "__main__":
    req = sample_request()
    json_data = high_quality_json()
    test_schema_validator_success()
    test_schema_validator_missing_field()
    test_quality_scoring_high(req, json_data)
    test_consistency_validator_day1_departure_error(req)
    print("ALL NARRATIVE VALIDATOR UNIT TESTS PASSED PERFECTLY!")
