"""Canonical Goa geography used by itinerary planning and hotel matching.

The public trip schema still uses the historical ``primary_island`` field for
backward compatibility, but Velqairn's Goa configuration treats it as a
canonical destination region/base rather than an island.
"""

DEFAULT_ARRIVAL_BASE = "Panaji"
DEFAULT_INTERMEDIATE_REGION = "North Goa"

GOA_REGION_TERMS: dict[str, tuple[str, ...]] = {
    "North Goa": (
        "north goa", "candolim", "calangute", "baga", "anjuna", "vagator",
        "morjim", "mandrem", "arambol", "aguada", "chapora", "ashwem",
        "mapusa", "saligao", "assagao", "siolim", "tiracol", "querim",
        "arpora", "bambolim", "bicholim", "fort aguada", "sinquerim",
        "mandrem beach", "ashwem beach", "arambol beach",
    ),
    "South Goa": (
        "south goa", "colva", "benaulim", "varca", "cavelossim", "mobor",
        "agonda", "palolem", "patnem", "cabo de rama", "netravali", "utorda",
        "majorda", "betalbatim", "canacona", "arossim", "vasco da gama",
        "bogmalo", "dabolim", "palelem",
    ),
    "Old Goa": (
        "old goa", "basilica of bom jesus", "bom jesus", "se cathedral",
        "divar", "divar island", "chorao", "chorao island", "ribandar",
    ),
    "Panaji": (
        "panaji", "panjim", "fontainhas", "miramar", "dona paula",
        "mandovi", "panaji waterfront", "mandovi river", "goa capital",
    ),
    "Dudhsagar": (
        "dudhsagar", "collem", "collem railway", "mollem", "spice plantation",
        "spice plantation belt",
    ),
}


def normalize_goa_region(value: str | None) -> str:
    """Return a canonical Goa region/base for a destination, attraction or hotel location."""
    text = str(value or "").strip().lower()
    if not text or text == "goa":
        return DEFAULT_ARRIVAL_BASE

    for region, terms in GOA_REGION_TERMS.items():
        if text == region.lower() or any(term in text for term in terms):
            return region

    if text in {"departure", "airport transfer"}:
        return "Departure"

    return str(value).strip()


def default_goa_region(day_index: int, total_days: int, selected_destinations: list[str] | None = None) -> str:
    """Choose a sensible deterministic default when a daily plan is incomplete."""
    if day_index == 0:
        return DEFAULT_ARRIVAL_BASE

    candidates = [normalize_goa_region(v) for v in (selected_destinations or []) if str(v).strip()]
    candidates = [v for v in candidates if v not in {"Panaji", "Departure"}]
    if candidates:
        return candidates[min(day_index - 1, len(candidates) - 1)]

    return DEFAULT_INTERMEDIATE_REGION
