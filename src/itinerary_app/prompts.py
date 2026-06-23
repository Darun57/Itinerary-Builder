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
- If information is missing, make sensible assumptions without calling attention to gaps.
"""


def _build_company_context(request: TripRequest) -> str:
    return build_company_context_for_request(request)


def build_user_prompt(request: TripRequest) -> str:
    company_context = _build_company_context(request)
    return f"""Create a travel itinerary using the details below.

Customer Name: {request.customer_name}
Destination: {request.destination}
Number of Nights: {request.number_of_nights}
Number of Days: {request.number_of_days}
Trip Type: {request.trip_type}
Budget Category: {request.budget_category}
Number of Adults: {request.number_of_adults}
Number of Children: {request.number_of_children}
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
Destination: {request.destination}
Duration: {request.number_of_days} days / {request.number_of_nights} nights
Trip Type: {request.trip_type}
Budget: {request.budget_category}
Travellers: {request.number_of_adults} adults, {request.number_of_children} children
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
"""
