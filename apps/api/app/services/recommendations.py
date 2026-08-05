from collections.abc import Callable
import re

import pandas as pd

from app.services.data_loader import (
    load_activities,
    load_destinations,
    load_ferries,
    load_hotels,
)
from app.schemas.trip import TripRequest


HOTEL_RESULT_COLUMNS = [
    "hotel_id",
    "hotel_name",
    "location",
    "category",
    "nightly_price",
    "suitable_for",
    "description",
    "score",
    "reason",
]
ACTIVITY_RESULT_COLUMNS = [
    "activity_id",
    "activity_name",
    "location",
    "price",
    "duration",
    "category",
    "description",
    "score",
    "reason",
]
FERRY_RESULT_COLUMNS = [
    "ferry_id",
    "operator",
    "from_location",
    "to_location",
    "departure_time",
    "arrival_time",
    "duration",
    "score",
    "reason",
]
DESTINATION_RESULT_COLUMNS = [
    "destination_name",
    "best_for",
    "description",
    "minimum_days",
    "maximum_days",
    "score",
    "reason",
]

ADVENTURE_TERMS = {"adventure", "scuba", "snorkeling", "diving", "watersport", "water sport", "trek"}
RELAXATION_TERMS = {"relax", "relaxation", "slow", "leisure", "peaceful", "beach", "sunset"}
SENIOR_TERMS = {"senior", "elder", "elderly", "old age", "low activity", "less walking"}
FAMILY_TERMS = {"family", "child", "children", "kid", "kids"}
HONEYMOON_TERMS = {"honeymoon", "couple", "romantic", "candlelight"}


def _normalize(value: object) -> str:
    return str(value or "").strip().lower()


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _request_text(request: TripRequest) -> str:
    parts = [
        request.destination,
        ", ".join(request.selected_destinations) if request.selected_destinations else "",
        " ".join([f"{dp.primary_island} {', '.join(dp.attractions)}" for dp in request.daily_island_plan]) if request.daily_island_plan else "",
        request.trip_type,
        request.budget_category,
        ", ".join(request.travel_style) if request.travel_style else "",
        request.trip_pace,
        request.hotel_category_preference,
        request.room_type_preference,
        request.room_view_preference,
        ", ".join(request.hotel_selection_islands) if request.hotel_selection_islands else "",
        ", ".join(request.selected_hotels) if request.selected_hotels else "",
        request.transfer_type,
        ", ".join(request.preferred_ferries) if request.preferred_ferries else "",
        request.meal_plan,
        ", ".join(request.food_preferences) if request.food_preferences else "",
        ", ".join(request.preferred_activities) if request.preferred_activities else "",
        ", ".join(request.special_occasions) if request.special_occasions else "",
        ", ".join(request.accessibility_requirements) if request.accessibility_requirements else "",
        ", ".join(request.restrictions_exclusions) if request.restrictions_exclusions else "",
        request.internal_staff_notes,
        request.special_requests,
    ]
    return " ".join([str(p) for p in parts if p]).lower()


def _budget_price_score(price: float, budget: str) -> int:
    if budget == "budget":
        if price <= 1000:
            return 35
        if price <= 6500:
            return 25
        if price <= 8500:
            return 10
        return -20
    if budget == "premium":
        if 5000 <= price <= 9000:
            return 30
        if price < 5000:
            return 15
        return 8
    if budget == "luxury":
        if price >= 9000:
            return 35
        if price >= 6500:
            return 20
        return 5
    return 0


def _append_reason(reasons: list[str], reason: str, score: int) -> int:
    reasons.append(reason)
    return score


def _clean_destination_label(text: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", str(text or "")).strip()


def _requested_locations(items: list[str]) -> set[str]:
    if not items:
        return set()
    if isinstance(items, str):
        items = [items]
    locations = set()
    for value in items:
        cleaned = _clean_destination_label(value)
        if cleaned:
            locations.add(_normalize(cleaned))
    return locations


def _daily_plan_locations(plan: list) -> set[str]:
    locations: set[str] = set()
    for dp in plan:
        if hasattr(dp, "primary_island") and dp.primary_island:
            locations.add(_normalize(_clean_destination_label(dp.primary_island)))
        if hasattr(dp, "attractions"):
            for att in dp.attractions:
                locations.add(_normalize(_clean_destination_label(att)))
    return locations


def _rank_rows(
    frame: pd.DataFrame,
    result_columns: list[str],
    score_row: Callable[[pd.Series], tuple[int, list[str]]],
    limit: int,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=result_columns)

    ranked_rows = []
    for _, row in frame.iterrows():
        score, reasons = score_row(row)
        ranked_row = row.to_dict()
        ranked_row["score"] = score
        ranked_row["reason"] = "; ".join(reasons) if reasons else "General company fallback match"
        ranked_rows.append(ranked_row)

    ranked = pd.DataFrame(ranked_rows)
    ranked = ranked.sort_values(["score"], ascending=False, kind="mergesort").head(limit)
    return ranked[result_columns].reset_index(drop=True)


def recommend_hotels(request: TripRequest, for_ui: bool = False) -> pd.DataFrame:
    hotels = load_hotels()
    request_text = _request_text(request)
    budget = _normalize(request.budget_category)
    trip_type = _normalize(request.trip_type)
    category_preference = _normalize(request.hotel_category_preference)
    preferred_locations = _daily_plan_locations(request.daily_island_plan)
    if not preferred_locations:
        preferred_locations = _requested_locations(request.hotel_selection_islands)
        if not preferred_locations and request.destination:
            preferred_locations.add(_normalize(_clean_destination_label(request.destination)))
        preferred_locations.update(_requested_locations(request.selected_destinations))
    selected_hotels = {value.lower() for value in request.selected_hotels if value and value.lower() != "none"}
    hotels = hotels[hotels["availability_status"].fillna("Available").str.lower() != "fully booked"].copy()
    if not for_ui and selected_hotels:
        selected_mask = hotels["hotel_name"].astype(str).str.lower().isin(selected_hotels)
        if selected_mask.any():
            hotels = hotels[selected_mask].copy()
    if preferred_locations:
        location_mask = hotels["location"].astype(str).str.lower().isin(preferred_locations)
        if location_mask.any():
            hotels = hotels[location_mask].copy()
    if category_preference:
        category_mask = hotels["category"].astype(str).str.lower() == category_preference
        if category_mask.any():
            hotels = hotels[category_mask].copy()

    def score_row(row: pd.Series) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        location = _normalize(row["location"])
        category = _normalize(row["category"])
        suitable_for = _normalize(row["suitable_for"])
        description = _normalize(row["description"])
        price = float(row["nightly_price"] or 0)
        availability = _normalize(row.get("availability_status") or "available")

        if availability == "limited availability":
            score += _append_reason(reasons, "limited availability but still bookable", 4)
        if preferred_locations and location in preferred_locations:
            score += _append_reason(reasons, "destination/location match", 25)
        if trip_type and trip_type in suitable_for:
            score += _append_reason(reasons, "suited to trip type", 30)
        if category_preference and category == category_preference:
            score += _append_reason(reasons, "matches selected hotel category", 45)
        elif budget == "budget" and category in {"3 star", "4 star"}:
            score += _append_reason(reasons, "budget-friendly hotel fit", 20)
        elif budget == "premium" and category in {"4 star", "5 star"}:
            score += _append_reason(reasons, "premium hotel fit", 20)
        elif budget == "luxury" and category in {"5 star", "ultra luxury"}:
            score += _append_reason(reasons, "luxury hotel fit", 25)

        score += _budget_price_score(price, budget)
        if budget:
            reasons.append("price aligned with budget")

        if _contains_any(request_text, HONEYMOON_TERMS) and (
            "honeymoon" in suitable_for or "boutique" in description or category in {"5 star", "ultra luxury"}
        ):
            score += _append_reason(reasons, "strong honeymoon fit", 25)
        if _contains_any(request_text, FAMILY_TERMS) and "family" in suitable_for:
            score += _append_reason(reasons, "family-friendly stay", 25)
        if _contains_any(request_text, RELAXATION_TERMS) and (
            "relax" in suitable_for or "quiet" in description or "beach" in description
        ):
            score += _append_reason(reasons, "relaxed stay profile", 15)
        if _contains_any(request_text, SENIOR_TERMS) and "easy access" in description:
            score += _append_reason(reasons, "lower-transfer senior-friendly base", 15)

        return score, reasons

    if hotels.empty:
        hotels = load_hotels()
        hotels = hotels[hotels["availability_status"].fillna("Available").str.lower() != "fully booked"].copy()

    # Request the full list ranked by score, then pick up to 20 per location and category for the UI sliders
    ranked = _rank_rows(hotels, HOTEL_RESULT_COLUMNS, score_row, limit=len(hotels))
    if not ranked.empty:
        ranked = ranked.groupby(["location", "category"]).head(20).reset_index(drop=True)
        ranked = ranked.sort_values(["score"], ascending=False, kind="mergesort")

    if ranked.empty:
        fallback = load_hotels()
        fallback = fallback[fallback["availability_status"].fillna("Available").str.lower() != "fully booked"].copy()
        ranked = _rank_rows(fallback, HOTEL_RESULT_COLUMNS, score_row, limit=len(fallback))
        ranked = ranked.groupby(["location", "category"]).head(20).reset_index(drop=True)
        ranked = ranked.sort_values(["score"], ascending=False, kind="mergesort")
        
    return ranked.head(100)


def recommend_activities(request: TripRequest) -> pd.DataFrame:
    activities = load_activities()
    request_text = _request_text(request)
    budget = _normalize(request.budget_category)
    destination = _normalize(request.destination)
    trip_type = _normalize(request.trip_type)
    limit = 5 if request.number_of_days >= 5 else 3

    def score_row(row: pd.Series) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        location = _normalize(row["location"])
        category = _normalize(row["category"])
        name = _normalize(row["activity_name"])
        description = _normalize(row["description"])
        price = float(row["price"] or 0)
        searchable = " ".join([name, category, description])

        if destination and (destination in location or location in destination):
            score += _append_reason(reasons, "destination/location match", 20)
        if budget:
            score += _budget_price_score(price, budget)
            reasons.append("activity price aligned with budget")

        if _contains_any(request_text, ADVENTURE_TERMS) and _contains_any(searchable, ADVENTURE_TERMS):
            score += _append_reason(reasons, "matches adventure request", 35)
        if _contains_any(request_text, RELAXATION_TERMS) and _contains_any(searchable, RELAXATION_TERMS):
            score += _append_reason(reasons, "matches relaxed pacing request", 25)
        if _contains_any(request_text, SENIOR_TERMS):
            if category in {"heritage", "beach", "nature", "water activity"} and price <= 1000:
                score += _append_reason(reasons, "gentler senior-friendly activity", 25)
            if category in {"adventure", "island tour"}:
                score -= 25
                reasons.append("reduced score for higher activity level")
        if trip_type == "family" or _contains_any(request_text, FAMILY_TERMS):
            if "family" in description or "children" in description or "non-swimmers" in description:
                score += _append_reason(reasons, "family-friendly activity", 25)
        if trip_type == "honeymoon" or _contains_any(request_text, HONEYMOON_TERMS):
            if category in {"beach", "adventure"} or "sunset" in searchable:
                score += _append_reason(reasons, "honeymoon-friendly experience", 20)
        if request.number_of_days >= 5 and category in {"island tour", "adventure", "water activity"}:
            score += _append_reason(reasons, "fits longer itinerary", 10)

        return score, reasons

    return _rank_rows(activities, ACTIVITY_RESULT_COLUMNS, score_row, limit=limit)


def recommend_ferries(request: TripRequest) -> pd.DataFrame:
    ferries = load_ferries()
    if ferries.empty:
        return pd.DataFrame(columns=FERRY_RESULT_COLUMNS)

    destination_recommendations = recommend_destinations(request)
    preferred_locations = [request.destination]
    preferred_locations.extend(destination_recommendations["destination_name"].head(3).tolist())
    preferred_text = " ".join(preferred_locations).lower()
    request_text = _request_text(request)
    limit = 4 if request.number_of_days >= 5 else 2

    def score_row(row: pd.Series) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        from_location = _normalize(row["from_location"])
        to_location = _normalize(row["to_location"])
        route_text = f"{from_location} {to_location}"

        if from_location in preferred_text or to_location in preferred_text:
            score += _append_reason(reasons, "connects recommended destination", 35)
        if "port blair" in from_location:
            score += _append_reason(reasons, "good arrival route", 15)
        if request.number_of_days >= 5 and "shaheed dweep" in route_text:
            score += _append_reason(reasons, "supports inter-island movement", 20)
        if request.number_of_days <= 4 and "port blair" in route_text and "swaraj dweep" in route_text:
            score += _append_reason(reasons, "efficient short-trip island transfer", 15)
        if _contains_any(request_text, SENIOR_TERMS) and "2 hours" in _normalize(row["duration"]):
            score -= 15
            reasons.append("reduced score for longer transfer")

        return score, reasons

    return _rank_rows(ferries, FERRY_RESULT_COLUMNS, score_row, limit=limit)


def recommend_destinations(request: TripRequest) -> pd.DataFrame:
    destinations = load_destinations()
    request_text = _request_text(request)
    destination = _normalize(request.destination)

    def score_row(row: pd.Series) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        name = _normalize(row["destination_name"])
        best_for = _normalize(row["best_for"])
        description = _normalize(row["description"])
        minimum_days = int(row["minimum_days"] or 0)
        maximum_days = int(row["maximum_days"] or 0)
        searchable = " ".join([name, best_for, description])

        if destination and (destination in name or name in destination or destination in description):
            score += _append_reason(reasons, "matches requested destination", 30)
        if minimum_days <= request.number_of_days and (
            maximum_days == 0 or request.number_of_days <= maximum_days + 2
        ):
            score += _append_reason(reasons, "fits trip duration", 25)
        if request.number_of_days >= minimum_days:
            score += 10
        if _contains_any(request_text, ADVENTURE_TERMS) and _contains_any(searchable, ADVENTURE_TERMS):
            score += _append_reason(reasons, "matches adventure interest", 25)
        if _contains_any(request_text, RELAXATION_TERMS) and _contains_any(searchable, RELAXATION_TERMS):
            score += _append_reason(reasons, "matches relaxation interest", 25)
        if _contains_any(request_text, HONEYMOON_TERMS) and (
            "honeymoon" in best_for or "beach" in searchable
        ):
            score += _append_reason(reasons, "strong honeymoon destination", 20)
        if _contains_any(request_text, FAMILY_TERMS) and "famil" in searchable:
            score += _append_reason(reasons, "family-friendly destination", 20)
        if _contains_any(request_text, SENIOR_TERMS):
            if name in {"port blair", "shaheed dweep", "chidiya tapu"}:
                score += _append_reason(reasons, "gentler senior-friendly destination", 20)
            if name == "baratang":
                score -= 25
                reasons.append("reduced score for longer road transfer")

        return score, reasons

    return _rank_rows(destinations, DESTINATION_RESULT_COLUMNS, score_row, limit=4)
