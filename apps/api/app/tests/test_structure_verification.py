import sys
import os
import json
import pypdf
from app.services.pdf_service import generate_luxury_pdf as generate_pdf

def test_itinerary_structure():
    trip_data = {
        "guest_name": "Puneet Kumar",
        "number_of_guests": 2,
        "number_of_adults": 2,
        "number_of_children": 0,
        "start_date": "2026-10-26",
        "end_date": "2026-10-30",
        "total_days": 5,
        "total_nights": 4,
        "room_count": 1,
        "price_per_person": 35000,
        "total_price": 70000,
        "hotel_tier": "Premium",
        "hotel_selection": "Specific",
        "hotel_option_type": "Standard",
        "season_type": "Regular",
        "pricing_source": "auto",
        "hotel_rooms": [{"island": "Port Blair", "hotel": "Symphony Samudra", "room_type": "Casa Room", "meal_plan": "CP", "nights": 1}],
        "pricing_breakdown": {
            "vehicle_cost": 15000,
            "ferry_cost": 8000,
            "activity_cost": 12000,
            "hotel_cost": 25000,
            "markup_amount": 10000,
            "total_package_price": 70000
        },
        "days": [
            {
                "day_number": 1,
                "title": "Cellular Jail Light & Sound Show & Cellular Jail Experience",
                "island": "Port Blair",
                "route": "Port Blair",
                "date": "26 Oct 2026",
                "visiting_places": "Upon arrival at Veer Savarkar International Airport in Port Blair, our representative will greet you and transfer you to your hotel. Later in the afternoon, visit the historic Cellular Jail, followed by the evocative Light and Sound Show in the evening.",
                "destination_story": "Port Blair, the capital of the Andaman and Nicobar Islands, holds profound historical significance. The Cellular Jail, also known as Kala Pani, stands as a poignant reminder of India's freedom struggle.",
                "todays_journey": "For the places highlighted above, private cab transfer will be provided. Pick up from airport to hotel, followed by sightseeing transfer to Cellular Jail and drop back to hotel.",
                "hotel_experience": "Overnight stay at Symphony Samudra, Port Blair. Enjoy the tranquil atmosphere and coastal charm.",
                "meals": "Dinner",
                "activities": ["Cellular Jail Visit", "Light & Sound Show"]
            },
            {
                "day_number": 2,
                "title": "Sunset at Radhanagar Beach",
                "island": "Havelock Island",
                "route": "Port Blair to Havelock Island",
                "date": "27 Oct 2026",
                "visiting_places": "Board the morning private ferry from Port Blair to Havelock Island. Upon arrival at Havelock jetty, our team will receive you and escort you to your beachside resort. In the late afternoon, head to Radhanagar Beach (Beach No. 7) to witness the world-famous sunset over the turquoise Andaman Sea.",
                "destination_story": "Havelock Island, officially Swaraj Dweep, is renowned for its powdery white sands and pristine coral reefs. Radhanagar Beach has been consistently rated among Asia's best beaches.",
                "todays_journey": "For the places highlighted above, private cab transfer will be provided from Port Blair hotel to jetty, Havelock jetty to resort, and evening excursion to Radhanagar Beach and return.",
                "hotel_experience": "Overnight stay at Symphony Palms Beach Resort, Havelock Island.",
                "meals": "Breakfast",
                "activities": ["Ferry Transfer", "Radhanagar Beach Sunset"]
            },
            {
                "day_number": 3,
                "title": "Elephant Beach Water Sports & Coral Reef Excursion",
                "island": "Havelock Island",
                "route": "Havelock Island",
                "date": "28 Oct 2026",
                "visiting_places": "After breakfast, head to Elephant Beach by speedboat. Engage in exhilarating water activities such as snorkeling and sea walk amidst colorful marine life.",
                "destination_story": "Elephant Beach is the epicenter of marine adventure on Havelock Island, famous for shallow crystal-clear waters and vibrant fringing reefs.",
                "todays_journey": "For the places highlighted above, private cab transfer will be provided between resort and Havelock jetty, along with round-trip boat transfer to Elephant Beach.",
                "hotel_experience": "Overnight stay at Symphony Palms Beach Resort, Havelock Island.",
                "meals": "Breakfast",
                "activities": ["Elephant Beach", "Snorkeling"]
            },
            {
                "day_number": 4,
                "title": "Natural Coral Bridge & Laxmanpur Beach Sunset",
                "island": "Neil Island",
                "route": "Havelock Island to Neil Island to Port Blair",
                "date": "29 Oct 2026",
                "visiting_places": "Take the ferry to Neil Island (Shaheed Dweep). Visit the famous Natural Rock Formation (Howrah Bridge) during low tide and the tranquil shores of Laxmanpur Beach before returning to Port Blair on the afternoon ferry.",
                "destination_story": "Neil Island offers a slow-paced, rustic charm with lush green paddy fields, tropical forests, and striking living rock bridges carved by centuries of ocean waves.",
                "todays_journey": "For the places highlighted above, private cab transfer will be provided across Neil Island sights and jetty transfers in both Havelock and Port Blair.",
                "hotel_experience": "Overnight stay at Symphony Samudra, Port Blair.",
                "meals": "Breakfast",
                "activities": ["Natural Bridge", "Laxmanpur Beach", "Ferry Transfer"]
            },
            {
                "day_number": 5,
                "title": "Departure",
                "island": "Port Blair",
                "route": "Port Blair",
                "date": "30 Oct 2026",
                "is_departure_day": True,
                "departure_narrative": "After breakfast, check out from the hotel with sweet memories of your Andaman holiday. Our driver will meet you at the hotel lobby and provide private transfer to Veer Savarkar International Airport in Port Blair for your onward flight home. We recommend arriving at the airport at least two hours prior to your scheduled flight departure.",
                "farewell_narrative": "Dear Puneet Kumar, we hope you had an unforgettable holiday exploring the pristine shores and rich history of the Andaman Islands. We sincerely thank you for choosing Darun Tourism as your travel partner. It has been our absolute pleasure hosting you, and we wish you a safe and pleasant journey ahead with memories to cherish for a lifetime.",
                "meals": "Breakfast",
                "activities": ["Airport Transfer"]
            }
        ]
    }

    from app.schemas.trip import TripRequest, DayPlan

    req = TripRequest(
        customer_name="Puneet Kumar",
        destination="Andaman",
        number_of_days=5,
        number_of_nights=4,
        arrival_date="2026-10-26",
        departure_date="2026-10-30",
        number_of_adults=2,
        number_of_children=0,
        per_person_cost=35000,
        total_package_cost=70000,
        daily_island_plan=[
            DayPlan(day_number=1, primary_island="Port Blair", attractions=["Cellular Jail"], activities=["Light & Sound Show"], hotel="Symphony Samudra", transfer_type="Private Cab"),
            DayPlan(day_number=2, primary_island="Havelock Island", attractions=["Radhanagar Beach"], activities=["Ferry Transfer"], hotel="Symphony Palms Beach Resort", transfer_type="Private Cab"),
            DayPlan(day_number=3, primary_island="Havelock Island", attractions=["Elephant Beach"], activities=["Snorkeling"], hotel="Symphony Palms Beach Resort", transfer_type="Private Cab"),
            DayPlan(day_number=4, primary_island="Neil Island", attractions=["Natural Bridge"], activities=["Laxmanpur Beach"], hotel="Symphony Samudra", transfer_type="Private Cab"),
            DayPlan(day_number=5, primary_island="Port Blair", attractions=["Airport"], activities=["Airport Transfer"], hotel="", transfer_type="Private Cab"),
        ]
    )

    itinerary_payload = json.dumps({"days": trip_data["days"]})

    output_path = "test_output_reference_check.pdf"
    print("Generating PDF...")
    pdf_bytes = generate_pdf(req, itinerary_payload)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Generated PDF successfully! File size: {len(pdf_bytes)} bytes.")

    # Read back PDF and verify structure
    reader = pypdf.PdfReader(output_path)
    print(f"Total pages: {len(reader.pages)}")

    full_text = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        full_text += f"\n--- PAGE {i+1} ---\n" + page_text

    # Print page contents for inspection
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if "DAY 1" in text:
            print(f"--- DAY 1 TEXT (Page {i+1}) ---")
            print(text)
        if "DAY 5" in text or "END OF THE JOURNEY" in text:
            print(f"--- DAY 5 TEXT (Page {i+1}) ---")
            print(text)

    # Assertions
    assert "Visiting Places And Destination Story" in full_text, "Missing Visiting Places And Destination Story"
    assert "Today's Journey" in full_text, "Missing Today's Journey"
    assert "Hotel Experience" in full_text, "Missing Hotel Experience"
    assert "Curated Experience" not in full_text, "Found Curated Experience which should be removed"
    assert "END OF THE JOURNEY" in full_text, "Missing END OF THE JOURNEY on departure day"
    assert "(Departure)" in full_text, "Missing (Departure) header tag"
    assert "Dear Puneet Kumar" in full_text, "Missing farewell guest personalization"
    assert "For the places highlighted above" in full_text, "Missing standard Today's Journey opening"

    print("ALL ASSERTIONS PASSED! PDF structure exactly matches the reference requirements.")

if __name__ == "__main__":
    test_itinerary_structure()
