from dataclasses import dataclass


@dataclass(frozen=True)
class TripRequest:
    customer_name: str
    lead_id: str
    customer_nationality: str
    customer_country: str
    customer_email: str
    customer_phone_number: str
    destination: str
    selected_destinations: str
    daily_island_plan: str
    number_of_nights: int
    number_of_days: int
    arrival_date: str
    departure_date: str
    travel_month: str
    flexible_travel_dates: bool
    trip_type: str
    budget_category: str
    number_of_adults: int
    number_of_children: int
    number_of_infants: int
    number_of_senior_citizens: int
    travel_style: str
    trip_pace: str
    hotel_category_preference: str
    room_type_preference: str
    room_view_preference: str
    hotel_selection_islands: str
    selected_hotels: str
    transfer_type: str
    preferred_ferries: str
    meal_plan: str
    food_preferences: str
    preferred_activities: str
    special_occasions: str
    accessibility_requirements: str
    restrictions_exclusions: str
    internal_staff_notes: str
    special_requests: str

