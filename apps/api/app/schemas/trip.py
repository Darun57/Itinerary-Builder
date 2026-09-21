import json
from typing import List, Optional
from pydantic import BaseModel, field_validator

NARRATIVE_SCHEMA_VERSION = "v2.0"


class CustomerContext(BaseModel):
    customer_name: str = ""
    lead_id: str = ""
    nationality: str = ""
    country: str = ""
    email: str = ""
    phone_number: str = ""


class DayPlan(BaseModel):
    day_number: int = 1
    primary_island: str = ""
    attractions: List[str] = []
    activities: List[str] = []
    hotel: str = ""
    transfer_type: str = ""
    ferry: str = ""
    ferry_timing: str = ""

    @field_validator("day_number", mode="before")
    @classmethod
    def parse_day_number(cls, v):
        if v == "" or v is None:
            return 1
        try:
            return int(v)
        except Exception:
            return 1

    @field_validator("attractions", "activities", mode="before")
    @classmethod
    def parse_plan_lists(cls, v):
        if v is None or v == "":
            return []
        return v


class TransportContext(BaseModel):
    transfer_type: str = ""
    preferred_ferries: List[str] = []
    meal_plan: str = ""
    food_preferences: List[str] = []


class IncludedActivity(BaseModel):
    activity_name: str = ""
    quantity: int = 1
    is_free: bool = True
    location: str = ""
    category: str = ""

    @field_validator("quantity", mode="before")
    @classmethod
    def parse_quantity(cls, v):
        if v == "" or v is None:
            return 1
        try:
            return int(v)
        except Exception:
            return 1


class PricingTier(BaseModel):
    category: str = "adult"
    label: Optional[str] = ""
    pax: int = 1
    cost: float = 0.0

    @field_validator("pax", mode="before")
    @classmethod
    def parse_pax(cls, v):
        if v == "" or v is None:
            return 1
        try:
            return int(v)
        except Exception:
            return 1

    @field_validator("cost", mode="before")
    @classmethod
    def parse_cost(cls, v):
        if v == "" or v is None:
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0


class TripRequest(BaseModel):
    customer_name: str = ""
    lead_id: str = ""
    customer_nationality: str = ""
    customer_country: str = ""
    customer_email: str = ""
    customer_phone_number: str = ""
    destination: str = ""
    selected_destinations: List[str] = []
    daily_island_plan: List[DayPlan] = []
    number_of_nights: int = 0
    number_of_days: int = 0
    arrival_date: str = ""
    departure_date: str = ""
    travel_month: str = ""
    flexible_travel_dates: bool = False
    trip_type: str = ""
    budget_category: str = ""
    number_of_adults: int = 0
    number_of_children: int = 0
    number_of_infants: int = 0
    number_of_senior_citizens: int = 0
    travel_style: List[str] = []
    trip_pace: str = ""
    hotel_category_preference: str = ""
    room_type_preference: str = ""
    room_view_preference: str = ""
    hotel_selection_islands: List[str] = []
    selected_hotels: List[str] = []
    transfer_type: str = ""
    preferred_ferries: List[str] = []
    meal_plan: str = ""
    food_preferences: List[str] = []
    flight_option: str = "Excluded"
    flight_per_person_rate: float = 0.0
    per_person_cost: float = 0.0
    child_cost: float = 0.0
    infant_cost: float = 0.0
    senior_cost: float = 0.0
    pricing_tiers: List[PricingTier] = []
    total_package_cost: float = 0.0
    preferred_activities: List[str] = []
    included_activities: List[IncludedActivity] = []
    special_occasions: List[str] = []
    accessibility_requirements: List[str] = []
    restrictions_exclusions: List[str] = []
    internal_staff_notes: str = ""
    special_requests: str = ""
    day_wise_style: Optional[str] = "luxury_narrative"

    @field_validator(
        "number_of_nights",
        "number_of_days",
        "number_of_adults",
        "number_of_children",
        "number_of_infants",
        "number_of_senior_citizens",
        mode="before",
    )
    @classmethod
    def parse_int_fields(cls, v):
        if v == "" or v is None:
            return 0
        try:
            return int(v)
        except Exception:
            return 0

    @field_validator(
        "flight_per_person_rate",
        "per_person_cost",
        "child_cost",
        "infant_cost",
        "senior_cost",
        "total_package_cost",
        mode="before",
    )
    @classmethod
    def parse_float_fields(cls, v):
        if v == "" or v is None:
            return 0.0
        try:
            return float(v)
        except Exception:
            return 0.0

    @field_validator(
        "selected_destinations",
        "travel_style",
        "hotel_selection_islands",
        "selected_hotels",
        "preferred_ferries",
        "food_preferences",
        "preferred_activities",
        "special_occasions",
        "accessibility_requirements",
        "restrictions_exclusions",
        "daily_island_plan",
        "pricing_tiers",
        "included_activities",
        mode="before",
    )
    @classmethod
    def parse_list_fields(cls, v):
        if v is None or v == "":
            return []
        return v


class DayItinerary(BaseModel):
    day_number: int
    title: str
    subtitle: str
    primary_island: str
    travel_movement: str
    visiting_places: Optional[str] = None
    destination_story: Optional[str] = None
    todays_journey: Optional[str] = None
    hotel_experience: Optional[str] = None
    curated_experience: Optional[str] = None
    expert_insider_notes: Optional[str] = None
    next_day_transition: Optional[str] = None
    departure_narrative: Optional[str] = None
    farewell_narrative: Optional[str] = None
    is_departure_day: Optional[bool] = False
    day_wise_style: Optional[str] = "luxury_narrative"
    summary_intro: Optional[str] = None
    operational_bullets: Optional[List[str]] = None
    morning: Optional[str] = None
    afternoon: Optional[str] = None
    evening: Optional[str] = None
    overnight: Optional[str] = None
    hotel: str
    activities: List[str]
    attractions: List[str]
    image_keyword: str


def parse_day_itineraries(payload: str) -> List[DayItinerary]:
    try:
        data = json.loads(payload)
        return [DayItinerary(**day) for day in data.get("days", [])]
    except Exception as exc:
        raise ValueError(f"Failed to parse itinerary JSON: {exc}") from exc
