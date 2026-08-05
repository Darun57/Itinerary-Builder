from dataclasses import dataclass, field
from typing import Any

from app.services.company_knowledge import build_recommendation_bundle
from app.schemas.trip import TripRequest, CustomerContext, DayPlan, TransportContext


@dataclass(frozen=True)
class TripMetadata:
    destination: str
    selected_destinations: list[str]
    daily_island_plan: list[DayPlan]
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
    hotel_stay_map: dict[str, int]
    transport: TransportContext
    travel_movements: list
    meal_preferences: list[str]
    special_requests: str
    special_occasions: list[str]
    accessibility_requirements: list[str]
    restrictions_exclusions: list[str]
    internal_staff_notes: str
    recommendations: RecommendationContext


def _first_value(values: list[str], fallback: str = "") -> str:
    return values[0] if values else fallback


def _normalize_island_name(island: str) -> str:
    if not island:
        return ""
    text = str(island).lower()
    if "havelock" in text or "swaraj" in text or "radhanagar" in text or "kalapathar" in text or "elephant beach" in text:
        return "Swaraj Dweep"
    if "neil" in text or "shaheed" in text or "laxmanpur" in text or "bharatpur" in text or "natural bridge" in text:
        return "Shaheed Dweep"
    if "baratang" in text or "limestone" in text or "mud volcano" in text:
        return "Baratang Island"
    if "diglipur" in text or "saddle peak" in text or "ross & smith" in text:
        return "Diglipur"
    if "port blair" in text or "cellular jail" in text or "corbyn" in text or "marina park" in text or "chidiya tapu" in text or "wandoor" in text or "museum" in text or "ross" in text or "north bay" in text:
        return "Port Blair"
    return str(island).strip()


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
            norm_loc = _normalize_island_name(location)
            mapping.setdefault(norm_loc, [])
            if hotel_name and hotel_name not in mapping[norm_loc]:
                mapping[norm_loc].append(hotel_name)
    return mapping


def _hotel_pool_by_island(recommendations) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    if recommendations is None or getattr(recommendations, "empty", True):
        return mapping
    for _, row in recommendations.iterrows():
        hotel_name = str(row.get("hotel_name") or "").strip()
        location = str(row.get("location") or "").strip()
        if location and hotel_name:
            norm_loc = _normalize_island_name(location)
            mapping.setdefault(norm_loc, [])
            if hotel_name not in mapping[norm_loc]:
                mapping[norm_loc].append(hotel_name)
    return mapping


def _normalize_destination(value: str) -> str:
    return str(value or "").strip().lower()


def _build_hotel_stay_map(daily_plan: list[DayPlan], selected_hotels_by_island: dict[str, list[str]], selected_hotels: list[str]) -> dict[str, int]:
    stay_map: dict[str, int] = {}
    hotel_cursor_by_island: dict[str, int] = {}
    def choose_hotel_for_island(island: str) -> str:
        norm_island = _normalize_island_name(island)
        hotels = selected_hotels_by_island.get(norm_island, [])
        if not hotels:
            hotels = [hotel for hotel in selected_hotels if hotel]
        if not hotels:
            return ""
        cursor = hotel_cursor_by_island.get(norm_island, 0)
        hotel = hotels[cursor % len(hotels)]
        hotel_cursor_by_island[norm_island] = cursor + 1
        return hotel

    current_island = ""
    current_hotel = ""
    current_stay_nights = 0

    def flush_current() -> None:
        nonlocal current_hotel, current_stay_nights
        if current_hotel and current_stay_nights > 0:
            stay_map[current_hotel] = stay_map.get(current_hotel, 0) + current_stay_nights
        current_hotel = ""
        current_stay_nights = 0

    for index, day_plan in enumerate(daily_plan):
        island = day_plan.primary_island or current_island
        if not island:
            island_keys = list(selected_hotels_by_island.keys())
            island = island_keys[0] if island_keys else ""
        if island != current_island:
            flush_current()
            current_island = island
            current_hotel = choose_hotel_for_island(island)
        if not current_hotel and selected_hotels:
            current_hotel = selected_hotels[min(index, len(selected_hotels) - 1)]
        current_stay_nights += 1

    flush_current()
    return stay_map


def _pick_hotel_for_day(
    day_plan: DayPlan,
    movement: Any,
    previous_hotel: str,
    previous_island: str,
    selected_hotels_by_island: dict[str, list[str]],
    hotel_pool_by_island: dict[str, list[str]],
    selected_hotels: list[str],
) -> str:
    norm_curr = _normalize_island_name(day_plan.primary_island)
    norm_prev = _normalize_island_name(previous_island)
    if previous_hotel and norm_curr and norm_curr == norm_prev:
        return previous_hotel
    candidates: list[str] = []
    islands: list[str] = [norm_curr]
    if movement:
        if movement.to_location:
            islands.append(_normalize_island_name(movement.to_location))
        if movement.from_location:
            islands.append(_normalize_island_name(movement.from_location))
    for island in islands:
        if island in selected_hotels_by_island:
            candidates.extend(selected_hotels_by_island[island])
        if island in hotel_pool_by_island:
            candidates.extend(hotel_pool_by_island[island])
    candidates.extend([hotel for hotel in selected_hotels if hotel not in candidates])
    candidates = [hotel for hotel in candidates if hotel]
    if candidates:
        return candidates[0]
    if previous_hotel:
        return previous_hotel
    return ""


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
        selected_destinations=request.selected_destinations,
        daily_island_plan=request.daily_island_plan,
        number_of_days=int(request.number_of_days or 0),
        number_of_nights=int(request.number_of_nights or 0),
        arrival_date=request.arrival_date,
        departure_date=request.departure_date,
        travel_month=request.travel_month,
        flexible_travel_dates=bool(request.flexible_travel_dates),
        trip_type=request.trip_type,
        budget_category=request.budget_category,
        travel_style=request.travel_style,
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
        preferred_ferries=request.preferred_ferries,
        meal_plan=request.meal_plan,
        food_preferences=request.food_preferences,
    )
    travel_movements = []
    selected_hotels = request.selected_hotels
    selected_hotels_by_island = _selected_hotels_by_island(bundle.hotels, selected_hotels)
    hotel_pool_by_island = _hotel_pool_by_island(bundle.hotels)
    daily_plan = request.daily_island_plan
    movement_by_day = {movement.day_number: movement for movement in travel_movements}
    enriched_plan: list[DayPlan] = []
    previous_hotel = ""
    previous_island = ""
    for day_plan in daily_plan:
        movement = movement_by_day.get(day_plan.day_number)
        hotel = _pick_hotel_for_day(
            day_plan=day_plan,
            movement=movement,
            previous_hotel=previous_hotel,
            previous_island=previous_island,
            selected_hotels_by_island=selected_hotels_by_island,
            hotel_pool_by_island=hotel_pool_by_island,
            selected_hotels=selected_hotels,
        )
        if not hotel and selected_hotels:
            hotel = selected_hotels[0]
        if not hotel and hotel_pool_by_island.get(day_plan.primary_island):
            hotel = hotel_pool_by_island[day_plan.primary_island][0]
        if not hotel and previous_hotel:
            hotel = previous_hotel
        enriched_plan.append(
            DayPlan(
                day_number=day_plan.day_number,
                primary_island=day_plan.primary_island,
                attractions=day_plan.attractions,
                activities=day_plan.activities,
                hotel=hotel,
                transfer_type=request.transfer_type,
            )
        )
        previous_hotel = hotel
        previous_island = day_plan.primary_island or previous_island
    daily_plan = enriched_plan
    hotel_stay_map = _build_hotel_stay_map(daily_plan, selected_hotels_by_island, selected_hotels)
    
    meal_prefs = [request.meal_plan]
    if isinstance(request.food_preferences, list):
        meal_prefs.extend(request.food_preferences)
        
    return TripContext(
        customer=customer,
        trip_metadata=trip_metadata,
        destinations=request.selected_destinations or [request.destination],
        daily_plan=daily_plan,
        activities=request.preferred_activities,
        selected_hotels=selected_hotels,
        selected_hotels_by_island=selected_hotels_by_island,
        hotel_stay_map=hotel_stay_map,
        transport=transport,
        travel_movements=travel_movements,
        meal_preferences=meal_prefs,
        special_requests=request.special_requests,
        special_occasions=request.special_occasions,
        accessibility_requirements=request.accessibility_requirements,
        restrictions_exclusions=request.restrictions_exclusions,
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


def get_day_movement(context: TripContext, day_number: int) -> Any | None:
    return None


def is_travel_day(context: TripContext, day_number: int) -> bool:
    day_plan = get_day(context, day_number)
    return bool(day_plan and day_plan.transfer_type and str(day_plan.transfer_type).lower() != "none")


def get_day_transport(context: TripContext, day_number: int) -> str:
    day_plan = get_day(context, day_number)
    return day_plan.transfer_type if day_plan else ""


def get_day_route(context: TripContext, day_number: int) -> str:
    return ""
