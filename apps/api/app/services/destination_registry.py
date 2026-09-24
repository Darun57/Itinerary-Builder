"""Additive destination registry for Velqairn.

This module is intentionally isolated from the existing Darun/Andaman data loader.
It resolves destination-scoped JSON data without changing the protected running path.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.schemas.destination_intelligence import (
    DestinationCapabilities,
    DestinationContractSummary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DESTINATION_ROOT = PROJECT_ROOT / "velqairn_destination_data"

# Canonical alias mapping for well-known variations
CANONICAL_ALIASES: dict[str, str] = {
    "rajasthan": "rajasthan",
    "jammu-and-kashmir": "jammu_and_kashmir",
    "jammu_and_kashmir": "jammu_and_kashmir",
    "jammu_kashmir": "jammu_and_kashmir",
    "kashmir": "jammu_and_kashmir",
    "jammu & kashmir": "jammu_and_kashmir",
    "jammu and kashmir": "jammu_and_kashmir",
    "goa": "goa",
    "kerala": "kerala",
    "himachal-pradesh": "himachal_pradesh",
    "himachal_pradesh": "himachal_pradesh",
    "himachal pradesh": "himachal_pradesh",
    "uttarakhand": "uttarakhand",
    "ladakh": "ladakh",
    "karnataka": "karnataka",
    "tamil-nadu": "tamil_nadu",
    "tamil_nadu": "tamil_nadu",
    "tamil nadu": "tamil_nadu",
    "sikkim": "sikkim",
    "maharashtra": "maharashtra",
}


def _get_discovered_mapping() -> dict[str, str]:
    """Dynamically scan DESTINATION_ROOT to discover all installed destination folders."""
    mapping = dict(CANONICAL_ALIASES)
    if DESTINATION_ROOT.exists():
        for item in DESTINATION_ROOT.iterdir():
            if item.is_dir() and (item / "config" / "destination.json").exists():
                folder_name = item.name
                slug = folder_name.replace("_", "-").lower()
                clean_key = folder_name.lower()
                mapping[slug] = folder_name
                mapping[clean_key] = folder_name
                mapping[folder_name.replace("-", "_").lower()] = folder_name
                # Also read config for explicit region_id if available
                try:
                    with (item / "config" / "destination.json").open("r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        reg_id = str(cfg.get("region_id", "")).strip().lower()
                        if reg_id:
                            mapping[reg_id] = folder_name
                            mapping[reg_id.replace("_", "-")] = folder_name
                        name = str(cfg.get("name", "")).strip().lower()
                        if name:
                            mapping[name] = folder_name
                except Exception:
                    pass
    return mapping


def is_additive_destination(region: str) -> bool:
    """Check if the given region is managed by the additive destination registry."""
    if not region:
        return False
    raw = str(region).strip().lower()
    cleaned = raw.replace(" ", "-")
    mapping = _get_discovered_mapping()
    return cleaned in mapping or raw in mapping or raw.replace(" ", "_") in mapping


def normalize_region(region: str) -> str:
    raw = str(region or "").strip().lower()
    cleaned = raw.replace(" ", "-")
    mapping = _get_discovered_mapping()
    if cleaned in mapping:
        return mapping[cleaned]
    if raw in mapping:
        return mapping[raw]
    raw_under = raw.replace(" ", "_").replace("-", "_")
    if raw_under in mapping:
        return mapping[raw_under]
    raise ValueError(f"Unsupported destination region: '{region}'. Not found in destination registry.")


def _load(region: str, collection: str, filename: str) -> list[dict[str, Any]]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / collection / filename
    if not path.exists():

        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return payload


def load_destinations(region: str) -> list[dict[str, Any]]:
    raw = _load(region, "destinations", "locations.json")
    out = []
    for item in raw:
        out.append({
            "destination_name": item.get("name"),
            **item,
        })
    return out


def load_attractions(region: str) -> list[dict[str, Any]]:
    return _load(region, "attractions", "attractions.json")


def load_activities(region: str) -> list[dict[str, Any]]:
    raw = _load(region, "activities", "activities.json")
    out = []
    for item in raw:
        loc_tail = item.get("destination_id", "").split(":")[-1].title()
        dur = f"{item.get('duration_minutes_min', 60)}-{item.get('duration_minutes_max', 120)} mins"
        price = "On Request" if item.get("price_status") == "supplier_required" else "Included"
        out.append({
            "activity_id": item.get("id"),
            "activity_name": item.get("name"),
            "location": loc_tail,
            "price": price,
            "duration": dur,
            "category": item.get("category", "sightseeing").title(),
            "description": " ".join(item.get("best_for", [])) or "Curated regional experience.",
            **item,
        })
    return out


def load_movements(region: str) -> list[dict[str, Any]]:
    return _load(region, "movements", "movements.json")


def load_day_plans(region: str) -> list[dict[str, Any]]:
    return _load(region, "day_plans", "day_plans.json")


def load_hotels(region: str) -> list[dict[str, Any]]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "hotels" / "hotels.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        return []
    records = []
    for item in payload:
        if isinstance(item, dict):
            rec = dict(item)
            if "name" in rec and "hotel_name" not in rec:
                rec["hotel_name"] = rec["name"]
            if "hotel_name" in rec and "name" not in rec:
                rec["name"] = rec["hotel_name"]
            if "id" in rec and "hotel_id" not in rec:
                rec["hotel_id"] = rec["id"]
            if "hotel_id" in rec and "id" not in rec:
                rec["id"] = rec["hotel_id"]
            if "location_id" in rec and "location" not in rec:
                loc = rec["location_id"].split(":")[-1].replace("_", " ").replace("-", " ").title()
                rec["location"] = loc
            records.append(rec)
    return records


def load_rooms(region: str) -> list[dict[str, Any]]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "rooms" / "rooms.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, list) else []


def load_config(region: str) -> dict[str, Any]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "config" / "destination.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_validation_rules(region: str) -> dict[str, Any]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "validation" / "rules.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_movement(region: str, from_id: str, to_id: str) -> Optional[dict[str, Any]]:
    """Resolve movement between two destination nodes within a region."""
    movements = load_movements(region)
    clean_from = from_id.strip().lower()
    clean_to = to_id.strip().lower()

    for m in movements:
        m_from = str(m.get("from_destination_id", "")).strip().lower()
        m_to = str(m.get("to_destination_id", "")).strip().lower()
        if (m_from == clean_from and m_to == clean_to) or (
            m_from.split(":")[-1] == clean_from.split(":")[-1]
            and m_to.split(":")[-1] == clean_to.split(":")[-1]
        ):
            return m
    return None


def get_location_by_id(region: str, location_id: str) -> Optional[dict[str, Any]]:
    locations = load_destinations(region)
    for loc in locations:
        if loc.get("id") == location_id or loc.get("id", "").split(":")[-1] == location_id.split(":")[-1]:
            return loc
    return None


def load_capabilities(region: str) -> dict[str, Any]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "config" / "capabilities.json"
    if not path.exists():
        return DestinationCapabilities().model_dump()
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
            # Validate through Pydantic
            caps = DestinationCapabilities(**raw)
            return caps.model_dump()
    except Exception:
        return DestinationCapabilities().model_dump()


def is_andaman_destination(region: Optional[str]) -> bool:
    """Check if the given region is Andaman or unspecified/legacy fallback."""
    if not region:
        return True
    raw = str(region).strip().lower()
    if "andaman" in raw:
        return True
    return not is_additive_destination(raw)


def get_destination_display_name(region: Optional[str]) -> str:
    """Resolve the clean display name of the destination."""
    if not region:
        return "Andaman Islands"
    raw = str(region).strip()
    if is_additive_destination(raw):
        try:
            cfg = load_config(raw)
            if cfg.get("name"):
                return str(cfg["name"]).strip()
        except Exception:
            pass
        return raw.replace("_", " ").replace("-", " ").title()
    if "andaman" in raw.lower():
        return "Andaman Islands"
    return raw.title()


def get_destination_base_location(region: Optional[str]) -> str:
    """Resolve the default entry/base location name for the destination."""
    if is_andaman_destination(region):
        return "Port Blair"
    try:
        caps = load_capabilities(str(region))
        base_id = caps.get("default_base_location_id")
        if base_id:
            loc = get_location_by_id(str(region), base_id)
            if loc and loc.get("name"):
                return str(loc["name"]).strip()
        locs = load_destinations(str(region))
        if locs and locs[0].get("name"):
            return str(locs[0]["name"]).strip()
    except Exception:
        pass
    return get_destination_display_name(region)


def verify_destination_contract(region: str) -> DestinationContractSummary:
    """Verify that a destination module satisfies the structural and content contract."""
    folder = normalize_region(region)
    cfg = load_config(region)
    name = cfg.get("name", folder.replace("_", " ").title())
    status = cfg.get("status", "scaffold")
    slug = cfg.get("region_id", folder.replace("_", "-"))

    caps_path = DESTINATION_ROOT / folder / "config" / "capabilities.json"
    has_capabilities = caps_path.exists()
    caps_data = load_capabilities(region) if has_capabilities else None
    caps_obj = DestinationCapabilities(**caps_data) if caps_data else None

    locations = load_destinations(region)
    attractions = load_attractions(region)
    activities = load_activities(region)
    movements = load_movements(region)
    day_plans = load_day_plans(region)
    hotels = load_hotels(region)

    missing = []
    if not (DESTINATION_ROOT / folder / "config" / "destination.json").exists():
        missing.append("config/destination.json")
    if not has_capabilities:
        missing.append("config/capabilities.json")

    # If marked active, require actual intelligence entities
    if status == "active":
        if len(locations) == 0:
            missing.append("destinations/locations.json (at least 1 location required)")
        if len(activities) == 0:
            missing.append("activities/activities.json (at least 1 activity required)")
        if len(movements) == 0:
            missing.append("movements/movements.json (at least 1 movement required)")
        if len(day_plans) == 0:
            missing.append("day_plans/day_plans.json (at least 1 day plan required)")

    satisfies = len(missing) == 0
    final_status = status
    if status == "active" and not satisfies:
        final_status = "incomplete"

    return DestinationContractSummary(
        slug=slug,
        name=name,
        status=final_status,
        has_config=(DESTINATION_ROOT / folder / "config" / "destination.json").exists(),
        has_capabilities=has_capabilities,
        capabilities=caps_obj,
        locations_count=len(locations),
        attractions_count=len(attractions),
        activities_count=len(activities),
        movements_count=len(movements),
        day_plans_count=len(day_plans),
        hotels_count=len(hotels),
        satisfies_contract=satisfies,
        missing_requirements=missing,
    )


def list_destinations(status_filter: Optional[str] = None) -> list[dict[str, Any]]:
    """List all installed destinations from DESTINATION_ROOT."""
    results = []
    seen = set()
    if not DESTINATION_ROOT.exists():
        return []

    for item in sorted(DESTINATION_ROOT.iterdir(), key=lambda p: p.name):
        if item.is_dir() and (item / "config" / "destination.json").exists():
            folder_name = item.name
            if folder_name in seen:
                continue
            seen.add(folder_name)
            try:
                summary = verify_destination_contract(folder_name)
                if status_filter and summary.status != status_filter:
                    continue
                results.append(summary.model_dump())
            except Exception:
                continue
    return results


def build_destination_context(region: str) -> dict[str, Any]:
    """Return a destination-scoped knowledge bundle for the AI/planner layer."""
    return {
        "config": load_config(region),
        "capabilities": load_capabilities(region),
        "destinations": load_destinations(region),
        "attractions": load_attractions(region),
        "activities": load_activities(region),
        "movements": load_movements(region),
        "day_plans": load_day_plans(region),
        "validation_rules": load_validation_rules(region),
        "hotels": load_hotels(region),
    }



# ITERATION 1: DestinationContext + AgencyContext
# Rules:
#   1. entry_hub resolved from locations data only; NEVER invented.
#   2. has_verified_ferry_movement is data-driven (movement records + trip plan).
#   3. Andaman is protected reference: hardcoded canonical values, unchanged.

from dataclasses import dataclass


@dataclass(frozen=True)
class AgencyContext:
    """Non-destination-varying agency facts. Legal entity fields are on DestinationContext."""
    bank_account_name: str = "ANDAMAN DARUN TOURS AND TRAVELS"
    bank_name: str = "HDFC BANK"
    account_number: str = "50200085886802 (CURRENT ACCOUNT)"
    ifsc: str = "HDFC0009508"
    upi_branch: str = "Bathubasti, Garacharma"
    proprietor_name: str = "Hemawathi"
    phone_primary: str = "+91 9474238991"
    phone_secondary: str = "+91 9933242718"


AGENCY_CONTEXT = AgencyContext()


@dataclass(frozen=True)
class DestinationContext:
    """
    Everything that changes per destination.
    entry_hub: None if unresolvable (NEVER fabricated).
    has_verified_ferry_movement: data-driven, not flag-driven.
    is_andaman: True only for the Andaman protected reference.
    """
    destination_id: str
    display_name: str
    is_andaman: bool
    agency_legal_name: str
    agency_location: str
    agency_email: str
    agency_website: str
    has_verified_ferry_movement: bool
    entry_hub: Optional[str]


def _resolve_entry_hub_from_data(region: str) -> Optional[str]:
    """Resolve entry hub from locations airport_name field. Returns None if absent."""
    try:
        caps = load_capabilities(region)
        base_id = str(caps.get("default_base_location_id") or "").strip()
        locs = load_destinations(region)
        for loc in locs:
            loc_id = str(loc.get("id") or "")
            if base_id and (loc_id == base_id or loc_id.split(":")[-1] == base_id.split(":")[-1]):
                airport_name = str(loc.get("airport_name") or "").strip()
                if airport_name:
                    return airport_name
        for loc in locs:
            airport_name = str(loc.get("airport_name") or "").strip()
            if airport_name:
                return airport_name
    except Exception:
        pass
    return None


def _has_verified_ferry_movement(region: str, trip: Any = None) -> bool:
    """
    True ONLY if movement catalog has maritime-mode record AND trip has non-empty ferry field.
    Andaman: always True. supports_ferry flag NOT consulted.
    """
    if is_andaman_destination(region):
        return True
    _maritime = {"ferry", "boat", "ship", "cruise", "speedboat", "houseboat"}
    try:
        movements = load_movements(region)
        catalog_has_ferry = any(
            str(m.get("mode") or m.get("mode_of_transport") or "").lower().strip() in _maritime
            for m in movements
        )
    except Exception:
        catalog_has_ferry = False
    if not catalog_has_ferry:
        return False
    if trip is not None:
        plans = list(getattr(trip, "daily_island_plan", None) or [])
        return any(str(getattr(day, "ferry", "") or "").strip() for day in plans)
    return catalog_has_ferry


def get_destination_context(destination: Optional[str], trip: Any = None) -> "DestinationContext":
    """Build DestinationContext. Andaman: hardcoded canonical. Additive: data-resolved."""
    if is_andaman_destination(destination):
        return DestinationContext(
            destination_id="andaman",
            display_name="Andaman Islands",
            is_andaman=True,
            agency_legal_name="Andaman Islands Darun Tours and Travels",
            agency_location="Andaman Islands, India",
            agency_email="andamandaruntourandtravels@gmail.com",
            agency_website="www.andamandaruntourism.in",
            has_verified_ferry_movement=True,
            entry_hub="Veer Savarkar International Airport, Port Blair",
        )
    dest_str = str(destination).strip()
    return DestinationContext(
        destination_id=dest_str.lower(),
        display_name=get_destination_display_name(dest_str),
        is_andaman=False,
        agency_legal_name="Darun Tourism",
        agency_location="India",
        agency_email="info@daruntourism.in",
        agency_website="www.daruntourism.in",
        has_verified_ferry_movement=_has_verified_ferry_movement(dest_str, trip),
        entry_hub=_resolve_entry_hub_from_data(dest_str),
    )
