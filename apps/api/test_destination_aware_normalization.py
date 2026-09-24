"""
Test Suite: Destination-Aware Itinerary Normalization & Andaman Isolation
Tests:
1. TEST 1 — GOA: 7D/6N Goa itinerary (both Simple & Luxury styles)
   Assert: ZERO Port Blair, Veer Savarkar, Havelock, Swaraj Dweep, Cellular Jail, DSS, Andaman Darun Tours and Travels
2. TEST 2 — RAJASTHAN: Rajasthan itinerary
   Assert: ZERO Andaman keywords / arrival / departure contamination
3. TEST 3 — KASHMIR: Kashmir itinerary
   Assert: ZERO Andaman keywords / arrival / departure contamination
4. TEST 4 — ANDAMAN REGRESSION: Canonical Andaman itinerary
   Assert: Port Blair arrival, Havelock/Swaraj Dweep, Andaman geography, and return ferry/flight intact
"""
import json
import unittest
from pathlib import Path
import sys

API_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(API_DIR))

from app.schemas.trip import TripRequest, DayPlan
from app.services.itinerary_normalizer import normalize_itinerary_payload
from app.services.google_service import generate_itinerary


ANDAMAN_FORBIDDEN_WORDS = [
    "port blair",
    "veer savarkar",
    "havelock",
    "swaraj dweep",
    "cellular jail",
    "dss",
    "andaman darun tours and travels",
    "andaman islands",
    "shaheed dweep",
    "neil island",
    "radhanagar",
    "corbyn",
    "chatham",
]


class TestDestinationAwareNormalization(unittest.TestCase):

    def test_1_goa_normalization_simple_style(self):
        """Test 1A: 7D/6N Goa itinerary in Simple Itinerary style."""
        req = TripRequest(
            customer_name="Rohan Verma",
            destination="Goa",
            number_of_days=7,
            number_of_nights=6,
            day_wise_style="simple_itinerary",
            selected_hotels=["Taj Fort Aguada Resort & Spa"],
            selected_destinations=["Candolim", "Panaji", "Old Goa", "Vagator"],
        )
        # Generate itinerary via google_service (fallback path with mock/empty api key)
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        normalized_data = json.loads(raw_result)
        days = normalized_data["days"]

        self.assertEqual(len(days), 7)

        # Check entire payload string for forbidden Andaman words
        payload_str = json.dumps(normalized_data).lower()
        for forbidden in ANDAMAN_FORBIDDEN_WORDS:
            self.assertNotIn(
                forbidden,
                payload_str,
                f"Contamination found in Goa Simple itinerary: '{forbidden}'"
            )

        # Day 1 Assertions
        day_1 = days[0]
        self.assertIn("Goa", day_1.get("title", "") + day_1.get("summary_intro", ""))
        self.assertNotIn("Port Blair", day_1.get("title", ""))
        self.assertNotIn("Port Blair", day_1.get("summary_intro", ""))
        bullets_d1 = " ".join(day_1.get("operational_bullets", []))
        self.assertIn("Arrival transfer to hotel", bullets_d1)
        self.assertNotIn("Port Blair", bullets_d1)

        # Day 7 (Departure) Assertions
        day_7 = days[6]
        self.assertTrue(day_7.get("is_departure_day"))
        self.assertNotIn("Port Blair", day_7.get("subtitle", ""))
        self.assertNotIn("Veer Savarkar", json.dumps(day_7))
        bullets_d7 = " ".join(day_7.get("operational_bullets", []))
        self.assertIn("Departure transfer to airport", bullets_d7)
        self.assertNotIn("Veer Savarkar", bullets_d7)
        self.assertNotIn("Port Blair", bullets_d7)
        self.assertIn("Darun Tourism", day_7.get("farewell_narrative", ""))
        self.assertNotIn("Andaman Darun Tours and Travels", day_7.get("farewell_narrative", ""))

    def test_1_goa_normalization_luxury_style(self):
        """Test 1B: 7D/6N Goa itinerary in Luxury Narrative style."""
        req = TripRequest(
            customer_name="Rohan Verma",
            destination="Goa",
            number_of_days=7,
            number_of_nights=6,
            day_wise_style="luxury_narrative",
            selected_hotels=["Taj Fort Aguada Resort & Spa"],
            selected_destinations=["Candolim", "Panaji", "Old Goa", "Vagator"],
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        normalized_data = json.loads(raw_result)
        days = normalized_data["days"]

        self.assertEqual(len(days), 7)
        payload_str = json.dumps(normalized_data).lower()
        for forbidden in ANDAMAN_FORBIDDEN_WORDS:
            self.assertNotIn(
                forbidden,
                payload_str,
                f"Contamination found in Goa Luxury itinerary: '{forbidden}'"
            )

        # Day 7 (Departure)
        day_7 = days[6]
        self.assertTrue(day_7.get("is_departure_day"))
        self.assertNotIn("port blair", day_7.get("departure_narrative", "").lower())
        self.assertNotIn("andaman", day_7.get("farewell_narrative", "").lower())
        self.assertIn("Darun Tourism", day_7.get("farewell_narrative", ""))

    def test_2_rajasthan_normalization(self):
        """Test 2: Rajasthan itinerary has zero Andaman contamination."""
        req = TripRequest(
            customer_name="Amitabh Sen",
            destination="Rajasthan",
            number_of_days=5,
            number_of_nights=4,
            day_wise_style="simple_itinerary",
            selected_hotels=["Rambagh Palace Jaipur"],
            selected_destinations=["Jaipur", "Udaipur"],
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        normalized_data = json.loads(raw_result)
        days = normalized_data["days"]

        self.assertEqual(len(days), 5)
        payload_str = json.dumps(normalized_data).lower()
        for forbidden in ANDAMAN_FORBIDDEN_WORDS:
            self.assertNotIn(
                forbidden,
                payload_str,
                f"Contamination found in Rajasthan itinerary: '{forbidden}'"
            )

        # Day 1 title should not be Port Blair
        day_1 = days[0]
        self.assertNotIn("Port Blair", day_1.get("title", ""))
        self.assertNotIn("Port Blair", day_1.get("summary_intro", ""))

        # Day 5 departure
        day_5 = days[4]
        self.assertTrue(day_5.get("is_departure_day"))
        self.assertNotIn("Port Blair", day_5.get("subtitle", ""))
        self.assertNotIn("Veer Savarkar", json.dumps(day_5))

    def test_3_kashmir_normalization(self):
        """Test 3: Jammu & Kashmir itinerary has zero Andaman contamination."""
        req = TripRequest(
            customer_name="Zoya Akhtar",
            destination="Jammu & Kashmir",
            number_of_days=5,
            number_of_nights=4,
            day_wise_style="simple_itinerary",
            selected_hotels=["The Khyber Himalayan Resort"],
            selected_destinations=["Srinagar", "Gulmarg"],
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        normalized_data = json.loads(raw_result)
        days = normalized_data["days"]

        self.assertEqual(len(days), 5)
        payload_str = json.dumps(normalized_data).lower()
        for forbidden in ANDAMAN_FORBIDDEN_WORDS:
            self.assertNotIn(
                forbidden,
                payload_str,
                f"Contamination found in Kashmir itinerary: '{forbidden}'"
            )

        day_1 = days[0]
        self.assertNotIn("Port Blair", day_1.get("title", ""))
        day_5 = days[4]
        self.assertTrue(day_5.get("is_departure_day"))
        self.assertNotIn("Port Blair", day_5.get("subtitle", ""))

    def test_4_andaman_regression_preserved(self):
        """Test 4: Andaman canonical behavior remains 100% intact."""
        req = TripRequest(
            customer_name="Karan Sharma",
            destination="Andaman Islands",
            number_of_days=4,
            number_of_nights=3,
            day_wise_style="simple_itinerary",
            selected_hotels=["Sinclairs Bayview", "Aquyas Hotel & Resort"],
            selected_destinations=["Port Blair", "Havelock Island", "Neil Island"],
            daily_island_plan=[
                DayPlan(
                    day_number=1,
                    primary_island="Port Blair",
                    attractions=["Corbyn's Cove Beach", "Cellular Jail & Light and Sound Show"],
                    activities=["Sightseeing"],
                    hotel="Sinclairs Bayview",
                ),
                DayPlan(
                    day_number=2,
                    primary_island="Swaraj Dweep (Havelock)",
                    attractions=["Radhanagar Beach", "Kalapathar Beach"],
                    activities=["Sunset Visit"],
                    hotel="Aquyas Hotel & Resort",
                    ferry="Makruzz Luxury Ferry",
                    ferry_timing="08:00 AM",
                ),
                DayPlan(
                    day_number=3,
                    primary_island="Shaheed Dweep (Neil)",
                    attractions=["Bharatpur Beach", "Natural Rock Arch", "Laxmanpur Beach"],
                    activities=["Beach Exploration"],
                    hotel="Aquyas Hotel & Resort",
                ),
                DayPlan(
                    day_number=4,
                    primary_island="Departure",
                    attractions=["Departure"],
                    activities=["Private Airport Transfer"],
                    hotel="",
                ),
            ],
        )
        raw_result = generate_itinerary(api_key="", model="gemini-2.5-flash", request=req)
        normalized_data = json.loads(raw_result)
        days = normalized_data["days"]

        self.assertEqual(len(days), 4)

        # Day 1: Must retain Port Blair arrival behavior
        day_1 = days[0]
        self.assertEqual(day_1.get("title"), "Arrival & Port Blair Sightseeing")
        self.assertIn("Pickup from Port Blair Airport and private transfer to hotel", day_1.get("operational_bullets", []))
        self.assertIn("Arrival at Port Blair", day_1.get("summary_intro", ""))

        # Day 2: Must retain Havelock island beaches and ferry
        day_2 = days[1]
        self.assertEqual(day_2.get("title"), "Radhanagar Beach & Sunset")
        bullets_d2 = day_2.get("operational_bullets", [])
        self.assertTrue(any("Ferry transfer to Swaraj Dweep (Havelock) via Makruzz Luxury Ferry" in b for b in bullets_d2))

        # Day 4: Departure must retain canonical Andaman departure
        day_4 = days[3]
        self.assertTrue(day_4.get("is_departure_day"))
        self.assertEqual(day_4.get("subtitle"), "Flight Departure from Port Blair")
        bullets_d4 = day_4.get("operational_bullets", [])
        self.assertIn("Private transfer to Veer Savarkar International Airport, Port Blair", bullets_d4)
        self.assertIn("Board scheduled return flight with memorable experiences of Andaman Darun Tours and Travels", bullets_d4)
        self.assertIn("Port Blair airport", day_4.get("todays_journey", ""))
        self.assertEqual(day_4.get("farewell_narrative"), "Thank you for traveling with Andaman Darun Tours and Travels.")


if __name__ == "__main__":
    unittest.main()
