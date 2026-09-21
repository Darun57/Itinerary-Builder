import urllib.request
import json

base_url = "http://127.0.0.1:8001/api"

req_data = {
    "customer_name": "Test User",
    "destination": "Andaman Islands",
    "number_of_days": 2,
    "number_of_nights": 1,
    "arrival_date": "2026-11-20",
    "departure_date": "2026-11-21",
    "trip_type": "Family Vacation",
    "budget_category": "Luxury",
    "number_of_adults": 2,
    "day_wise_style": "simple_itinerary",
    "selected_hotels": ["Sinclairs Bayview"],
    "daily_island_plan": [
        {
            "day_number": 1,
            "primary_island": "Port Blair",
            "attractions": ["Corbyn's Cove Beach", "Cellular Jail"],
            "activities": ["Sightseeing"],
            "hotel": "Sinclairs Bayview",
            "transfer_type": "Private AC Cab"
        },
        {
            "day_number": 2,
            "primary_island": "Departure",
            "attractions": ["Departure"],
            "activities": ["Private Airport Transfer"],
            "hotel": "",
            "transfer_type": "Private AC Cab"
        }
    ]
}

data_bytes = json.dumps(req_data).encode("utf-8")
req = urllib.request.Request(f"{base_url}/ai/generate", data=data_bytes, headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("[SUCCESS] Live server /ai/generate responded!")
        print(f"Itinerary length: {len(res['itinerary_text'])} chars")

        pdf_req_data = {"request": req_data, "itinerary_text": res["itinerary_text"]}
        pdf_req = urllib.request.Request(f"{base_url}/pdf/generate", data=json.dumps(pdf_req_data).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pdf_req, timeout=30) as pdf_resp:
            pdf_bytes = pdf_resp.read()
            print(f"[SUCCESS] Live server /pdf/generate responded with {len(pdf_bytes)} bytes of PDF!")
except Exception as e:
    print("[INFO] Live server connection result:", e)
