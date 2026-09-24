"""Validation engine for destination intelligence and namespace isolation.

Ensures no cross-destination entity leakage, verifies location-hotel relationships,
movement feasibility, and prevents invalid combinations.
"""
from __future__ import annotations

from typing import Any, List, Optional
from app.schemas.destination_intelligence import ValidationResult
from app.services.destination_registry import (
    is_additive_destination,
    load_destinations,
    load_attractions,
    load_activities,
    load_movements,
    load_hotels,
    normalize_region,
)


class DestinationValidationError(ValueError):
    """Raised when destination constraint or namespace validation fails."""
    pass


def validate_namespace(region: str, entity_id: str) -> bool:
    """Check that an entity ID strictly starts with the expected destination namespace."""
    if not entity_id:
        return True
    expected_prefix = f"{normalize_region(region)}:"
    # Also handle normalized variant with hyphen if needed
    alt_prefix = f"{normalize_region(region).replace('_', '-')}:"
    return entity_id.startswith(expected_prefix) or entity_id.startswith(alt_prefix)


def validate_hotel_location(region: str, hotel_name_or_id: str, location_id: str) -> ValidationResult:
    """
    Validate that a hotel belongs to the specified location.
    If hotel belongs to another location (e.g. Jaipur hotel in Udaipur), flag validation error.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not hotel_name_or_id or not location_id:
        return ValidationResult(is_valid=True)

    clean_loc = location_id.strip().lower()
    clean_hotel = hotel_name_or_id.strip().lower()

    # If it's an additive destination, check hotel catalog if available
    if is_additive_destination(region):
        hotels = load_hotels(region)
        matching_hotel = None
        for h in hotels:
            if h.get("id", "").lower() == clean_hotel or h.get("name", "").lower() == clean_hotel:
                matching_hotel = h
                break

        if matching_hotel:
            hotel_loc = matching_hotel.get("location_id", "").lower()
            if hotel_loc and hotel_loc != clean_loc and hotel_loc.split(":")[-1] != clean_loc.split(":")[-1]:
                errors.append(
                    f"VALIDATION ERROR: Hotel '{hotel_name_or_id}' belongs to location '{hotel_loc}', "
                    f"not selected location '{location_id}'."
                )

    # Heuristic check for city names in hotel name vs selected location
    # E.g., if hotel has "Jaipur" in name but location is "Udaipur"
    known_cities = ["jaipur", "jodhpur", "udaipur", "jaisalmer", "pushkar", "bikaner", "srinagar", "gulmarg", "pahalgam"]
    loc_tail = clean_loc.split(":")[-1]
    
    for city in known_cities:
        if city in clean_hotel and city != loc_tail:
            errors.append(
                f"VALIDATION ERROR: Hotel '{hotel_name_or_id}' indicates location '{city}', "
                f"which conflicts with selected location '{loc_tail}'."
            )
            break

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


from app.services.destination_registry import (
    is_additive_destination,
    load_destinations,
    load_attractions,
    load_activities,
    load_movements,
    load_hotels,
    load_capabilities,
    normalize_region,
)


def validate_trip_destination_integrity(
    region: str,
    selected_locations: list[str],
    daily_plan: list[dict[str, Any]],
) -> ValidationResult:
    """Validate full itinerary against destination intelligence rules and capabilities."""
    errors: list[str] = []
    warnings: list[str] = []

    if not is_additive_destination(region):
        # Andaman or non-additive destination — handled by its own protected validator
        return ValidationResult(is_valid=True)

    norm_region = normalize_region(region)
    destinations = load_destinations(region)
    caps = load_capabilities(region)

    valid_locations = {loc["id"].lower() for loc in destinations}
    valid_loc_names = {loc["name"].lower() for loc in destinations}
    valid_loc_tails = {loc["id"].split(":")[-1].lower() for loc in destinations}

    # 1. Location Validation
    for loc in selected_locations:
        loc_str = str(loc).strip().lower()
        if not (loc_str in valid_locations or loc_str in valid_loc_names or loc_str in valid_loc_tails):
            errors.append(f"Location '{loc}' does not belong to destination '{region}'.")

    # 2. Daily Plan Validation & Capabilities
    for idx, dp in enumerate(daily_plan):
        day_num = dp.get("day_number", idx + 1)
        loc = str(dp.get("primary_island") or dp.get("location") or "").strip().lower()
        hotel = str(dp.get("hotel") or "").strip()
        ferry = str(dp.get("ferry") or "").strip()
        activities = dp.get("activities") or []

        # Check hotel location consistency
        if hotel and loc and hotel.lower() not in ["none", ""]:
            hotel_check = validate_hotel_location(region, hotel, loc)
            if not hotel_check.is_valid:
                errors.extend([f"Day {day_num}: {err}" for err in hotel_check.errors])

        # Capability: Ferry check
        if not caps.get("supports_ferry", False) and ferry and ferry.lower() not in ["none", ""]:
            errors.append(f"Day {day_num}: Destination '{region}' does not support ferries ('{ferry}' requested).")

        # Capability: Houseboat check
        if not caps.get("supports_houseboat", False) and "houseboat" in hotel.lower():
            errors.append(f"Day {day_num}: Destination '{region}' does not support houseboat stays ('{hotel}').")

        # Capability: High altitude acclimatization check (e.g. Ladakh)
        if caps.get("requires_acclimatization_logic", False) and day_num == 1:
            base_loc = caps.get("default_base_location_id", "")
            base_tail = base_loc.split(":")[-1].lower() if base_loc else ""
            if loc and base_tail and loc != base_tail and loc != base_loc.lower():
                errors.append(
                    f"Day 1: High-altitude destination '{region}' requires mandatory base acclimatization at "
                    f"'{base_tail.title()}', but Day 1 is scheduled at '{loc.title()}'."
                )

        # Cross-destination entity leakage check in activities
        for act in activities:
            act_str = str(act).lower()
            # If activity explicitly references another region namespace
            for other_reg in ["rajasthan", "goa", "kashmir", "jammu", "kerala", "andaman", "ladakh"]:
                if other_reg != norm_region and other_reg != norm_region.replace("_", "-"):
                    if f"{other_reg}:" in act_str:
                        errors.append(
                            f"Day {day_num}: Cross-destination leakage detected. "
                            f"Activity '{act}' from '{other_reg}' cannot be included in '{region}' trip."
                        )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

