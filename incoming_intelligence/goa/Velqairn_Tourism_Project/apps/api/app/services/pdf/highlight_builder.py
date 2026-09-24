"""
Trip highlight data extraction and section builder.
"""
from app.schemas.trip import TripRequest
from app.services.pdf.text_utils import (
    split_values,
    unique_values,
    format_list,
    clean_destination_label,
)
from app.services.pdf.constants import ITINERARY_KEYWORDS


def _extract_activity_terms(text: str) -> list[str]:
    activity_terms: list[str] = []
    lower_text = str(text or "").lower()
    for keyword, label in ITINERARY_KEYWORDS.items():
        if keyword in lower_text and label not in activity_terms:
            activity_terms.append(label)
    return activity_terms


def _daily_plan_places(daily_island_plan: list) -> list[str]:
    places: list[str] = []
    if not isinstance(daily_island_plan, list):
        return places
    for dp in daily_island_plan:
        if not hasattr(dp, "primary_island"):
            continue
        if getattr(dp, "primary_island", None):
            places.append(clean_destination_label(dp.primary_island))
        for att in getattr(dp, "attractions", None) or []:
            places.append(clean_destination_label(att))
    return unique_values(places)


def _extract_itinerary_destinations(itinerary_text: str) -> list[str]:
    destinations: list[str] = []
    for raw_line in itinerary_text.splitlines():
        lower_line = raw_line.lower()
        for keyword in [
            "panaji", "fontainhas", "old goa", "divar island", "candolim",
            "calangute", "baga", "anjuna", "vagator", "chapora", "morjim",
            "ashwem", "mandrem", "arambol", "aguada", "grand island",
            "bogmalo", "majorda", "colva", "benaulim", "varca", "cavelossim",
            "mobor", "agonda", "palolem", "patnem", "cabo de rama",
            "netravali", "dudhsagar", "collem", "ponda", "miramar",
        ]:
            if keyword in lower_line:
                destinations.append(clean_destination_label(keyword.title()))
    return unique_values(destinations)


def highlight_data(itinerary_text: str, request: TripRequest) -> dict[str, object]:
    destinations = unique_values(
        [clean_destination_label(v) for v in split_values(request.selected_destinations)]
        + _daily_plan_places(request.daily_island_plan)
        + _extract_itinerary_destinations(itinerary_text)
    )
    if not destinations:
        destinations = [clean_destination_label(request.destination or "Goa")]
    return {
        "destinations": destinations,
        "activities": unique_values(split_values(request.preferred_activities) + _extract_activity_terms(itinerary_text)),
        "travel_style": unique_values(split_values(request.travel_style) + split_values(request.trip_type)),
        "selected_hotels": unique_values(split_values(request.selected_hotels)),
        "meal_preferences": unique_values([request.meal_plan] + split_values(request.food_preferences)),
        "transport_preferences": unique_values([request.transfer_type] + split_values(request.preferred_ferries)),
        "special_occasions": unique_values(split_values(request.special_occasions)),
        "hotel_category": str(request.hotel_category_preference or request.budget_category or "Selected").strip(),
        "duration": f"{request.number_of_days} Days / {request.number_of_nights} Nights",
        "pace": str(request.trip_pace or "Balanced").strip(),
        "budget": str(request.budget_category or "").strip(),
    }


def highlight_sections(itinerary_text: str, request: TripRequest) -> list[dict[str, str]]:
    data = highlight_data(itinerary_text, request)
    from app.services.pdf.text_utils import format_list_short
    
    dest_full = format_list(data["destinations"], request.destination or "Goa")
    dest_short = format_list_short(data["destinations"], 45, request.destination or "Goa")
    
    act_full = format_list(data["activities"], request.preferred_activities or "Selected activities")
    act_short = format_list_short(data["activities"], 45, request.preferred_activities or "Selected activities")
    
    travel_style = format_list(data["travel_style"], request.trip_type or "Luxury")
    
    hotels_full = format_list(data["selected_hotels"], f"{data['hotel_category']} stays")
    hotels_short = format_list_short(data["selected_hotels"], 45, f"{data['hotel_category']} stays")
    
    meals_full = format_list(data["meal_preferences"], request.meal_plan or "Selected meal plan")
    meals_short = format_list_short(data["meal_preferences"], 45, request.meal_plan or "Selected meal plan")
    
    transport_full = format_list(data["transport_preferences"], request.transfer_type or "Selected transfers")
    transport_short = format_list_short(data["transport_preferences"], 45, request.transfer_type or "Selected transfers")
    
    occasions = format_list(data["special_occasions"], request.special_occasions or "Guest occasions")

    return [
        {
            "title": "DESTINATIONS COVERED",
            "value": dest_short,
            "description": f"Explore {dest_full} across a carefully sequenced {data['duration']} island journey.",
        },
        {
            "title": "TOP ACTIVITIES",
            "value": act_short,
            "description": f"Experience {act_full} with experiences matched to the selected travel style and guest preferences.",
        },
        {
            "title": "TRAVEL STYLE",
            "value": f"{travel_style} | {data['pace']} Pace",
            "description": f"The itinerary follows a {travel_style} style with a {data['pace'].lower()} pace.",
        },
        {
            "title": "HOTEL EXPERIENCE",
            "value": f"{data['hotel_category']} | {hotels_short}",
            "description": f"Guests will stay in {hotels_full} with the requested {data['hotel_category']} positioning.",
        },
        {
            "title": "TRANSPORT EXPERIENCE",
            "value": transport_short,
            "description": f"Transfers are planned around {transport_full} for smooth island connectivity.",
        },
        {
            "title": "DINING AND OCCASIONS",
            "value": f"{meals_short} | {occasions}",
            "description": f"Meal planning reflects {meals_full} and the selected guest occasions.",
        },
    ]
