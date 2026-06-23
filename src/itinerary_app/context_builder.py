import pandas as pd

from itinerary_app.models import TripRequest


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _format_bullets(items: list[str]) -> str:
    if not items:
        return "- No strong company-listed options found."
    return "\n".join(f"- {item}" for item in items)


def _format_hotels(hotels: pd.DataFrame) -> str:
    if hotels.empty:
        return _format_bullets([])

    items = []
    for _, row in hotels.iterrows():
        hotel_name = _clean_text(row.get("hotel_name"))
        location = _clean_text(row.get("location"))
        category = _clean_text(row.get("category"))
        suitable_for = _clean_text(row.get("suitable_for")).replace(";", ", ")
        description = _clean_text(row.get("description"))
        reason = _clean_text(row.get("reason"))
        item = (
            f"{hotel_name} in {location} ({category}). "
            f"Best suited for {suitable_for}. {description} "
            f"Selection note: {reason}."
        )
        items.append(item)
    return _format_bullets(items)


def _format_activities(activities: pd.DataFrame) -> str:
    if activities.empty:
        return _format_bullets([])

    items = []
    for _, row in activities.iterrows():
        activity_name = _clean_text(row.get("activity_name"))
        location = _clean_text(row.get("location"))
        duration = _clean_text(row.get("duration"))
        category = _clean_text(row.get("category"))
        description = _clean_text(row.get("description"))
        reason = _clean_text(row.get("reason"))
        item = (
            f"{activity_name} in {location} ({category}, around {duration}). "
            f"{description} Selection note: {reason}."
        )
        items.append(item)
    return _format_bullets(items)


def _format_ferries(ferries: pd.DataFrame) -> str:
    if ferries.empty:
        return _format_bullets([])

    items = []
    for _, row in ferries.iterrows():
        operator = _clean_text(row.get("operator"))
        from_location = _clean_text(row.get("from_location"))
        to_location = _clean_text(row.get("to_location"))
        departure_time = _clean_text(row.get("departure_time"))
        arrival_time = _clean_text(row.get("arrival_time"))
        duration = _clean_text(row.get("duration"))
        reason = _clean_text(row.get("reason"))
        item = (
            f"{operator}: {from_location} to {to_location}, departing {departure_time}, "
            f"arriving {arrival_time}, duration {duration}. Selection note: {reason}."
        )
        items.append(item)
    return _format_bullets(items)


def _format_destinations(destinations: pd.DataFrame) -> str:
    if destinations.empty:
        return _format_bullets([])

    items = []
    for _, row in destinations.iterrows():
        destination_name = _clean_text(row.get("destination_name"))
        best_for = _clean_text(row.get("best_for")).replace(";", ", ")
        description = _clean_text(row.get("description"))
        minimum_days = _clean_text(row.get("minimum_days"))
        maximum_days = _clean_text(row.get("maximum_days"))
        reason = _clean_text(row.get("reason"))
        if minimum_days and maximum_days:
            if minimum_days == "0":
                stay_text = f"Typical stay up to {maximum_days} days."
            else:
                stay_text = f"Typical stay {minimum_days} to {maximum_days} days."
        else:
            stay_text = "Typical stay varies by itinerary."
        item = (
            f"{destination_name}: best for {best_for}. {description} "
            f"{stay_text} Selection note: {reason}."
        )
        items.append(item)
    return _format_bullets(items)


def _format_business_rules() -> str:
    rules = [
        "Prefer company-listed hotels, activities, ferries, and destinations over invented options.",
        "Use company inventory whenever it fits the request.",
        "Keep the itinerary tone professional, polished, and luxury-oriented.",
        "Do not include hotel rates, package prices, or activity pricing unless explicitly requested.",
        "Do not add booking instructions, payment steps, or operational notes for the customer.",
        "If an exact match is limited, stay close to the recommended company inventory before using generic filler.",
    ]
    return _format_bullets(rules)


def build_company_context(
    request: TripRequest,
    hotels: pd.DataFrame,
    activities: pd.DataFrame,
    ferries: pd.DataFrame,
    destinations: pd.DataFrame,
) -> str:
    special_requests = _clean_text(request.special_requests) or "None"
    trip_summary = "\n".join(
        [
            "Trip Request",
            f"- Customer: {_clean_text(request.customer_name)}",
            f"- Destination: {_clean_text(request.destination)}",
            f"- Duration: {request.number_of_days} days / {request.number_of_nights} nights",
            f"- Trip Type: {_clean_text(request.trip_type)}",
            f"- Budget Category: {_clean_text(request.budget_category)}",
            f"- Travellers: {request.number_of_adults} adults, {request.number_of_children} children",
            f"- Special Requests: {special_requests}",
        ]
    )

    sections = [
        trip_summary,
        "Recommended Destinations\n" + _format_destinations(destinations),
        "Recommended Hotels\n" + _format_hotels(hotels),
        "Recommended Activities\n" + _format_activities(activities),
        "Recommended Ferries\n" + _format_ferries(ferries),
        "Business Rules\n" + _format_business_rules(),
    ]
    return "\n\n".join(sections)
