from itinerary_app.company_knowledge import build_company_context_for_request
from itinerary_app.models import TripRequest


SYSTEM_PROMPT = """You are an expert luxury travel consultant writing itineraries for internal staff use.

Create a polished, professional, customer-friendly itinerary for an Andaman tour.

Rules:
- Output only the itinerary text.
- Use company-provided hotels, activities, ferries, and destination guidance whenever available.
- Do not invent hotels, activities, ferries, or destinations when strong company-listed options exist.
- Do not include pricing, flight tickets, package costs, or booking instructions.
- Use a clear structure with a trip title and day-wise plans.
- Match the tone of a premium luxury travel agency.
- Keep the format easy to edit in a text editor.
- Include Morning, Afternoon, Evening, and Overnight Stay for every day.
- Strongly prioritize the selected destinations and daily island plan when planning the route.
- Use internal staff notes to improve the itinerary, but never mention them in the final customer-facing output.
- If information is missing, make sensible assumptions without calling attention to gaps.
"""


def _build_company_context(request: TripRequest) -> str:
    return build_company_context_for_request(request)


def build_user_prompt(request: TripRequest) -> str:
    company_context = _build_company_context(request)
    return f"""Create a travel itinerary using the details below.

Customer Name: {request.customer_name}
Lead ID: {request.lead_id}
Customer Nationality: {request.customer_nationality}
Customer Country: {request.customer_country}
Customer Email: {request.customer_email}
Customer Phone Number: {request.customer_phone_number}
Destination: {request.destination}
Selected Destinations / Sightseeing Spots: {request.selected_destinations or 'None'}
Daily Island Plan: {request.daily_island_plan or 'None'}
Number of Nights: {request.number_of_nights}
Number of Days: {request.number_of_days}
Arrival Date: {request.arrival_date}
Departure Date: {request.departure_date}
Travel Month: {request.travel_month}
Flexible Travel Dates: {"Yes" if request.flexible_travel_dates else "No"}
Trip Type: {request.trip_type}
Budget Category: {request.budget_category}
Number of Adults: {request.number_of_adults}
Number of Children: {request.number_of_children}
Number of Infants: {request.number_of_infants}
Number of Senior Citizens: {request.number_of_senior_citizens}
Travel Style: {request.travel_style or 'None'}
Trip Pace: {request.trip_pace}
Hotel Category Preference: {request.hotel_category_preference}
Room Type Preference: {request.room_type_preference}
Room View Preference: {request.room_view_preference}
Transfer Type: {request.transfer_type or 'None'}
Preferred Ferries: {request.preferred_ferries or 'None'}
Meal Plan: {request.meal_plan or 'None'}
Food Preferences: {request.food_preferences or 'None'}
Preferred Activities: {request.preferred_activities or 'None'}
Special Occasions: {request.special_occasions or 'None'}
Accessibility Requirements: {request.accessibility_requirements or 'None'}
Restrictions / Exclusions: {request.restrictions_exclusions or 'None'}
Internal Staff Notes: {request.internal_staff_notes or 'None'}
Special Requests: {request.special_requests or 'None'}

Company context:
{company_context}

Formatting requirements:
- Start with a Trip Title.
- Then generate Day 1 through Day {request.number_of_days}.
- Each day must include these sections exactly:
  - Morning
  - Afternoon
  - Evening
  - Overnight Stay
- Keep each section concise but descriptive.
- Do not add any notes before or after the itinerary.
- Prefer company-recommended hotels, activities, ferries, and destinations from the context above.
- Do not invent hotels or activities if the company context already provides suitable options.
- Do not include pricing, package costs, booking instructions, or payment language.
- Use internal staff notes to influence planning, but do not mention them explicitly.
- Prioritize the selected destinations and daily island plan as the routing backbone.
"""


def build_messages(request: TripRequest) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(request)},
    ]


def build_prompt_text(request: TripRequest) -> str:
    return f"{SYSTEM_PROMPT}\n\n{build_user_prompt(request)}"


def build_fast_prompt_text(request: TripRequest) -> str:
    company_context = _build_company_context(request)
    return f"""Write a concise, editable Andaman travel itinerary.

Customer: {request.customer_name}
Lead ID: {request.lead_id}
Nationality: {request.customer_nationality}
Country: {request.customer_country}
Email: {request.customer_email}
Phone: {request.customer_phone_number}
Destination: {request.destination}
Selected Destinations / Sightseeing Spots: {request.selected_destinations or 'None'}
Daily Island Plan: {request.daily_island_plan or 'None'}
Duration: {request.number_of_days} days / {request.number_of_nights} nights
Arrival Date: {request.arrival_date}
Departure Date: {request.departure_date}
Travel Month: {request.travel_month}
Flexible Travel Dates: {"Yes" if request.flexible_travel_dates else "No"}
Trip Type: {request.trip_type}
Budget: {request.budget_category}
Travellers: {request.number_of_adults} adults, {request.number_of_children} children
Infants: {request.number_of_infants}
Senior Citizens: {request.number_of_senior_citizens}
Travel Style: {request.travel_style or 'None'}
Trip Pace: {request.trip_pace}
Hotel Category Preference: {request.hotel_category_preference}
Room Type Preference: {request.room_type_preference}
Room View Preference: {request.room_view_preference}
Transfer Type: {request.transfer_type or 'None'}
Preferred Ferries: {request.preferred_ferries or 'None'}
Meal Plan: {request.meal_plan or 'None'}
Food Preferences: {request.food_preferences or 'None'}
Preferred Activities: {request.preferred_activities or 'None'}
Special Occasions: {request.special_occasions or 'None'}
Accessibility Requirements: {request.accessibility_requirements or 'None'}
Restrictions / Exclusions: {request.restrictions_exclusions or 'None'}
Internal Staff Notes: {request.internal_staff_notes or 'None'}
Special Requests: {request.special_requests or 'None'}

Company context:
{company_context}

Rules:
- Output only the itinerary text.
- Start with a Trip Title.
- Generate Day 1 through Day {request.number_of_days}.
- Each day must include exactly: Morning, Afternoon, Evening, Overnight Stay.
- Keep every section to one short sentence.
- Prefer company-listed hotels, activities, ferries, and destinations from the context above.
- Do not invent hotels or activities if company options are already available.
- Do not include pricing, flight tickets, package costs, booking instructions, or payment language.
- Use internal staff notes to influence planning, but do not mention them explicitly.
- Prioritize the selected destinations and daily island plan as the routing backbone.
"""
