import pytest
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
        destination="Goa",
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
                "title": "Day 1: Arrival in Panaji",
                "subtitle": "Warm Tropical Welcome",
                "primary_island": "Panaji",
                "travel_movement": "Airport Private Driver Transfer",
                "destination_story": "A warm tropical ocean breeze greets you as you touch down at Goa airport in Panaji. Your private driver greets you with fresh garlands before heading through lush palm-lined coastal roads to your resort.",
                "todays_journey": "Private luxury vehicle transfer from Airport to Taj Exotica Resort & Spa takes approximately 25 minutes. Smooth coastal drive with scenic harbor views.",
                "curated_experience": "Afternoon sunset stroll along Dona Paula's Cove beach followed by private photography session during golden hour over the Bay of Bengal.",
                "hotel_experience": "Check into Taj Exotica Resort & Spa for a luxurious villa experience with private plunge pool and personalized concierge welcome amenities.",
                "expert_insider_notes": "Carry crisp INR currency notes as local island shops near cellular jail have limited card terminal network connectivity.",
                "next_day_transition": "Tomorrow morning features an early private luxury private chauffeur transfer to North Goa to North Goa Island.",
                "hotel": "Taj Exotica Resort & Spa",
                "activities": ["Dona Paula's Cove Beach Stroll"],
                "attractions": ["Basilica of Bom Jesus"],
                "image_keyword": "goa_beach"
            },
            {
                "day_number": 2,
                "title": "Departure",
                "is_departure_day": True,
                "subtitle": "Farewell to Paradise",
                "primary_island": "Panaji",
                "travel_movement": "Private Driver Airport Transfer",
                "departure_narrative": "Enjoy a peaceful morning check-out at Taj Exotica Resort & Spa with luggage assistance. Your private chauffeur will transfer you to Goa airport for your scheduled flight home.",
                "farewell_narrative": "Darun Tourism extends its heartfelt gratitude to Aarav Sharma and family for choosing us. It was our genuine pleasure crafting your Goa journey, and we look forward to welcoming you back.",
                "expert_insider_notes": "Arrive at airport 2 hours prior to scheduled departure time due to security queues.",
                "next_day_transition": "Safe travels on your return flight carrying lifelong memories of your luxury Goa getaway.",
                "hotel": "Taj Exotica Resort & Spa",
                "activities": ["Souvenir Shopping"],
                "attractions": ["Local Market"],
                "image_keyword": "goa_sunset"
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
            "primary_island": "Panaji",
            "destination_story": "Heading to return flight.",
            "todays_journey": "Transfer to airport for return flight."
        },
        {
            "day_number": 2,
            "title": "Day 2: Departure",
            "primary_island": "Panaji",
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
