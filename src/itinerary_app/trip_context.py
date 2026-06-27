from dataclasses import dataclass, field
from typing import Any

from itinerary_app.company_knowledge import build_recommendation_bundle
from itinerary_app.models import TripRequest


@dataclass(frozen=True)
class CustomerContext:
    customer_name: str
    lead_id: str
    nationality: str
    country: str
    email: str
    phone_number: str


@dataclass(frozen=True)
class TripMetadata:
    destination: str
    selected_destinations: list[str]
    daily_island_plan: list[dict[str, list[str]]]
    number_of_days: int
    number_of_nights: int
    arrival_date: str
    departure_date: str
    travel_month: str
    flexible_travel_dates: bool
    trip_type: str
    budget_category: str
    travel_style: list[str]
    trip_pace: str
    room_type_preference: str
    room_view_preference: str
    hotel_category_preference: str
    number_of_adults: int
    number_of_children: int
    number_of_infants: int
    number_of_senior_citizens: int


@dataclass(frozen=True)
class DayPlan:
    day_number: int
    primary_island: str
    attractions: list[str]
    activities: list[str]
    hotel: str
    transfer_type: str


@dataclass(frozen=True)
class TransportContext:
    transfer_type: str
    preferred_ferries: list[str]
    meal_plan: str
    food_preferences: list[str]


@dataclass(frozen=True)
class RecommendationContext:
    destinations: list[dict[str, Any]] = field(default_factory=list)
    hotels: list[dict[str, Any]] = field(default_factory=list)
    activities: list[dict[str, Any]] = field(default_factory=list)
    ferries: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TripContext:
    customer: CustomerContext
    trip_metadata: TripMetadata
    destinations: list[str]
    daily_plan: list[DayPlan]
    activities: list[str]
    selected_hotels: list[str]
    selected_hotels_by_island: dict[str, list[str]]
    transport: TransportContext
    meal_preferences: list[str]
    special_requests: str
    special_occasions: list[str]
    accessibility_requirements: list[str]
    restrictions_exclusions: list[str]
    internal_staff_notes: str
    recommendations: RecommendationContext


def _split_values(text: str) -> list[str]:
    values: list[str] = []
    for chunk in str(text or "").replace("\n", ",").split(","):
        cleaned = chunk.strip()
        if cleaned and cleaned.lower() != "none":
            values.append(cleaned)
    return values


def _first_value(values: list[str], fallback: str = "") -> str:
    return values[0] if values else fallback


def _infer_day_hotel(day_number: int, request: TripRequest, selected_hotels_by_island: dict[str, list[str]]) -> str:
    day_plan_line = ""
    for raw_line in str(request.daily_island_plan or "").splitlines():
        if raw_line.lower().startswith(f"day {day_number}"):
            day_plan_line = raw_line
            break
    if ":" in day_plan_line:
        _, raw_values = day_plan_line.split(":", 1)
        destinations = [value.strip() for value in raw_values.split(",") if value.strip()]
        for destination in destinations:
            if destination in selected_hotels_by_island and selected_hotels_by_island[destination]:
                return selected_hotels_by_island[destination][0]
    return ""


def _parse_daily_plan(text: str) -> list[DayPlan]:
    plan: list[DayPlan] = []
    for raw_line in str(text or "").splitlines():
        if ":" in raw_line:
            label, raw_values = raw_line.split(":", 1)
        else:
            label, raw_values = raw_line, ""
        destinations = [value.strip() for value in raw_values.split(",") if value.strip()]
        day_text = label.strip().lower()
        day_number = 0
        if day_text.startswith("day "):
            try:
                day_number = int(day_text.split()[1])
            except (IndexError, ValueError):
                day_number = len(plan) + 1
        else:
            day_number = len(plan) + 1
        primary_island = _first_value(destinations, "")
        attractions = destinations[1:] if len(destinations) > 1 else []
        plan.append(
            DayPlan(
                day_number=day_number,
                primary_island=primary_island,
                attractions=attractions,
                activities=[],
                hotel="",
                transfer_type="",
            )
        )
    return plan


def _day_plan_as_dict(day_plan: DayPlan) -> dict[str, list[str]]:
    values = [value for value in [day_plan.primary_island, *day_plan.attractions, *day_plan.activities] if value]
    return {f"Day {day_plan.day_number}": values}


def _selected_hotels_by_island(recommendations, selected_hotels: list[str]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    if recommendations is None or getattr(recommendations, "empty", True):
        return mapping
    selected = {hotel.lower() for hotel in selected_hotels}
    for _, row in recommendations.iterrows():
        hotel_name = str(row.get("hotel_name") or "").strip()
        location = str(row.get("location") or "").strip()
        if selected and hotel_name.lower() not in selected:
            continue
        if location:
            mapping.setdefault(location, [])
            if hotel_name and hotel_name not in mapping[location]:
                mapping[location].append(hotel_name)
    return mapping


def _recommendation_rows(frame) -> list[dict[str, Any]]:
    if frame is None or getattr(frame, "empty", True):
        return []
    return [row.to_dict() for _, row in frame.iterrows()]


def build_trip_context(request: TripRequest) -> TripContext:
    bundle = build_recommendation_bundle(request)
    customer = CustomerContext(
        customer_name=request.customer_name,
        lead_id=request.lead_id,
        nationality=request.customer_nationality,
        country=request.customer_country,
        email=request.customer_email,
        phone_number=request.customer_phone_number,
    )
    trip_metadata = TripMetadata(
        destination=request.destination,
        selected_destinations=_split_values(request.selected_destinations),
        daily_island_plan=_parse_daily_plan(request.daily_island_plan),
        number_of_days=int(request.number_of_days or 0),
        number_of_nights=int(request.number_of_nights or 0),
        arrival_date=request.arrival_date,
        departure_date=request.departure_date,
        travel_month=request.travel_month,
        flexible_travel_dates=bool(request.flexible_travel_dates),
        trip_type=request.trip_type,
        budget_category=request.budget_category,
        travel_style=_split_values(request.travel_style),
        trip_pace=request.trip_pace,
        room_type_preference=request.room_type_preference,
        room_view_preference=request.room_view_preference,
        hotel_category_preference=request.hotel_category_preference,
        number_of_adults=int(request.number_of_adults or 0),
        number_of_children=int(request.number_of_children or 0),
        number_of_infants=int(request.number_of_infants or 0),
        number_of_senior_citizens=int(request.number_of_senior_citizens or 0),
    )
    transport = TransportContext(
        transfer_type=request.transfer_type,
        preferred_ferries=_split_values(request.preferred_ferries),
        meal_plan=request.meal_plan,
        food_preferences=_split_values(request.food_preferences),
    )
    selected_hotels = _split_values(request.selected_hotels)
    selected_hotels_by_island = _selected_hotels_by_island(bundle.hotels, selected_hotels)
    daily_plan = _parse_daily_plan(request.daily_island_plan)
    daily_plan = [
        DayPlan(
            day_number=day_plan.day_number,
            primary_island=day_plan.primary_island,
            attractions=day_plan.attractions,
            activities=day_plan.activities,
            hotel=_infer_day_hotel(day_plan.day_number, request, selected_hotels_by_island),
            transfer_type=request.transfer_type,
        )
        for day_plan in daily_plan
    ]
    return TripContext(
        customer=customer,
        trip_metadata=trip_metadata,
        destinations=_split_values(request.selected_destinations) or [request.destination],
        daily_plan=daily_plan,
        activities=_split_values(request.preferred_activities),
        selected_hotels=selected_hotels,
        selected_hotels_by_island=selected_hotels_by_island,
        transport=transport,
        meal_preferences=[request.meal_plan] + _split_values(request.food_preferences),
        special_requests=request.special_requests,
        special_occasions=_split_values(request.special_occasions),
        accessibility_requirements=_split_values(request.accessibility_requirements),
        restrictions_exclusions=_split_values(request.restrictions_exclusions),
        internal_staff_notes=request.internal_staff_notes,
        recommendations=RecommendationContext(
            destinations=_recommendation_rows(bundle.destinations),
            hotels=_recommendation_rows(bundle.hotels),
            activities=_recommendation_rows(bundle.activities),
            ferries=_recommendation_rows(bundle.ferries),
        ),
    )


def get_day(context: TripContext, day_number: int) -> DayPlan | None:
    for day_plan in context.daily_plan:
        if day_plan.day_number == day_number:
            return day_plan
    return None


def get_primary_island(context: TripContext, day_number: int) -> str:
    day_plan = get_day(context, day_number)
    return day_plan.primary_island if day_plan else ""


def get_day_attractions(context: TripContext, day_number: int) -> list[str]:
    day_plan = get_day(context, day_number)
    return list(day_plan.attractions) if day_plan else []


def get_day_hotel(context: TripContext, day_number: int) -> str:
    day_plan = get_day(context, day_number)
    return day_plan.hotel if day_plan else ""
