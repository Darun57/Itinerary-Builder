import json
import urllib.request
import fitz  # PyMuPDF

req_payload = {
    "customer_name": "Mr. Karan",
    "lead_id": "ADT-UHBNA",
    "customer_email": "darun00444@gmail.com",
    "customer_phone_number": "9933268774",
    "customer_nationality": "Indian",
    "destination": "Andaman Islands",
    "selected_destinations": [
        "Port Blair", "Swaraj Dweep (Havelock)", "Shaheed Dweep (Neil)"
    ],
    "number_of_days": 5,
    "number_of_nights": 4,
    "arrival_date": "2026-10-18",
    "departure_date": "2026-10-22",
    "budget_category": "Premium Luxury",
    "travel_style": ["Family Vacation"],
    "trip_pace": "Relaxed Pace",
    "number_of_adults": 2,
    "number_of_children": 0,
    "hotel_category_preference": "Boutique",
    "room_type_preference": "Villa",
    "meal_plan": "MAP",
    "food_preferences": ["Non-Vegetarian", "Vegetarian"],
    "special_occasions": ["Honeymoon / Anniversary"],
    "transfer_type": "Private",
    "preferred_ferries": ["Makruzz", "Green Ocean"],
    "day_wise_style": "simple",
    "preferred_activities": [
        "Cellular Jail Light and Sound Show",
        "Scuba Diving Introductory Dive",
        "Radhanagar Beach Sunset Visit"
    ],
    "included_activities": [
        {"activity_name": "Shore Scuba Diving (Beginner / DSD)", "quantity": 2, "is_free": True},
        {"activity_name": "Sea Walk at Elephant Beach", "quantity": 1, "is_free": True}
    ],
    "selected_hotels": [
        "SeaShell Samssara", "Taj Exotica Resort & Spa", "Silver Sand Beach Resort"
    ],
    "total_package_cost": 82000,
    "per_person_cost": 16000,
    "flight_option": "Included",
    "flight_per_person_rate": 25000,
    "daily_island_plan": [
        {
            "day_number": 1,
            "primary_island": "Port Blair",
            "attractions": ["Cellular Jail", "Corbyn's Cove Beach"],
            "activities": ["Cellular Jail Light and Sound Show"],
            "hotel": "SeaShell Samssara",
            "transfer_type": "Private",
            "ferry": "",
            "ferry_timing": ""
        },
        {
            "day_number": 2,
            "primary_island": "Swaraj Dweep (Havelock)",
            "attractions": ["Radhanagar Beach", "Kalapathar Beach"],
            "activities": ["Radhanagar Beach Sunset Visit"],
            "hotel": "Taj Exotica Resort & Spa",
            "transfer_type": "Private",
            "ferry": "Makruzz (Port Blair to Swaraj Dweep)",
            "ferry_timing": "06:00 AM"
        },
        {
            "day_number": 3,
            "primary_island": "Swaraj Dweep (Havelock)",
            "attractions": ["Elephant Beach"],
            "activities": ["Scuba Diving Introductory Dive"],
            "hotel": "Taj Exotica Resort & Spa",
            "transfer_type": "Private",
            "ferry": "",
            "ferry_timing": ""
        },
        {
            "day_number": 4,
            "primary_island": "Shaheed Dweep (Neil)",
            "attractions": ["Natural Rock Bridge", "Laxmanpur Beach", "Bharatpur Beach"],
            "activities": ["Laxmanpur Beach Sunset"],
            "hotel": "Silver Sand Beach Resort",
            "transfer_type": "Private",
            "ferry": "Green Ocean (Swaraj Dweep to Shaheed Dweep)",
            "ferry_timing": "09:20 AM"
        },
        {
            "day_number": 5,
            "primary_island": "Port Blair",
            "attractions": ["Departure"],
            "activities": ["Airport Transfer"],
            "hotel": "Silver Sand Beach Resort",
            "transfer_type": "Private",
            "ferry": "Makruzz (Shaheed Dweep to Port Blair)",
            "ferry_timing": "10:00 AM"
        }
    ]
}

# 1. Call AI generate to get itinerary json
ai_req = urllib.request.Request(
    'http://127.0.0.1:8001/api/ai/generate',
    data=json.dumps(req_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print("Calling /api/ai/generate...")
with urllib.request.urlopen(ai_req) as response:
    ai_data = json.loads(response.read().decode('utf-8'))

itinerary_text = ai_data.get("itinerary_text", "")
print("AI generation complete. Sample itinerary snippet:")
print(itinerary_text[:300])

# 2. Call PDF generate
pdf_payload = {
    "request": req_payload,
    "itinerary_text": itinerary_text
}
pdf_req = urllib.request.Request(
    'http://127.0.0.1:8001/api/pdf/generate',
    data=json.dumps(pdf_payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print("\nCalling /api/pdf/generate...")
with urllib.request.urlopen(pdf_req) as pdf_resp:
    pdf_bytes = pdf_resp.read()

output_pdf_path = "app/tests/output_andaman_test.pdf"
with open(output_pdf_path, "wb") as f:
    f.write(pdf_bytes)

print(f"Saved PDF to {output_pdf_path}, size = {len(pdf_bytes)} bytes.")

# 3. Inspect PDF with PyMuPDF
doc = fitz.open(output_pdf_path)
print(f"Total Pages: {len(doc)}")

goa_words = ["panaji", "fontainhas", "calangute", "baga", "candolim", "vagator", "anjuna", "mandovi", "goadarun"]
found_goa_words = []

for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text().strip()
    image_list = page.get_images()
    
    is_blank = len(text) < 100 and len(image_list) == 0
    print(f"Page {page_num + 1}: length {len(text)} chars, {len(image_list)} images, Blank: {is_blank}")
    
    lower_text = text.lower()
    for gw in goa_words:
        if gw in lower_text:
            found_goa_words.append((page_num + 1, gw))

print("\n--- Validation Results ---")
if found_goa_words:
    print(f"ERROR: Found Goa keywords: {found_goa_words}")
else:
    print("SUCCESS: Zero Goa keywords found!")

blank_pages = [p + 1 for p in range(len(doc)) if len(doc[p].get_text().strip()) < 100 and len(doc[p].get_images()) == 0]
if blank_pages:
    print(f"ERROR: Blank overflow pages detected: {blank_pages}")
else:
    print("SUCCESS: Zero blank overflow pages detected!")

for d in range(1, 6):
    p_idx = 2 + d
    if p_idx < len(doc):
        imgs = doc[p_idx].get_images()
        print(f"Day {d} (Page {p_idx + 1}): {len(imgs)} image(s)")
doc.close()
