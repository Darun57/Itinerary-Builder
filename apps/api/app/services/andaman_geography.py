"""Canonical Andaman Islands geography used by itinerary planning and hotel matching."""

DEFAULT_ARRIVAL_BASE = "Port Blair"
DEFAULT_INTERMEDIATE_REGION = "Swaraj Dweep (Havelock)"

ANDAMAN_REGION_TERMS: dict[str, tuple[str, ...]] = {
    "Port Blair": (
        "port blair", "veer savarkar", "cellular jail", "ross island",
        "north bay", "corbyn's cove", "wandoor", "chidiya tapu",
        "munda pahar", "south andaman", "chatham", "aberdeen bazaar",
    ),
    "Swaraj Dweep (Havelock)": (
        "havelock", "swaraj dweep", "radhanagar", "beach no 7", "elephant beach",
        "kalapathar", "beach 5", "vijaynagar", "govindnagar",
    ),
    "Shaheed Dweep (Neil)": (
        "neil island", "neil", "shaheed dweep", "bharatpur beach",
        "natural bridge", "sitapur beach", "laxmanpur beach",
    ),
    "Baratang": (
        "baratang", "limestone caves", "mud volcano", "parrot island",
        "mangrove creek", "jolly buoy",
    ),
    "Diglipur": (
        "diglipur", "ross and smith", "saddle peak", "ramnagar",
        "kalipur beach", "turtle nesting",
    ),
    "Long Island": ("long island", "lalaji bay", "merk bay"),
    "Little Andaman": ("little andaman", "hut bay", "butler bay"),
    "Rangat": ("rangat", "amkunj beach", "cuthbert bay"),
    "Mayabunder": ("mayabunder", "karmatang", "avis island"),
}


def normalize_andaman_island(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if not text or text in {"andaman", "andaman islands", "andaman & nicobar"}:
        return DEFAULT_ARRIVAL_BASE
    for region, terms in ANDAMAN_REGION_TERMS.items():
        if text == region.lower() or any(term in text for term in terms):
            return region
    if text in {"departure", "airport transfer"}:
        return "Departure"
    return str(value).strip()


def default_andaman_island(day_index: int, total_days: int, selected_destinations: list[str] | None = None) -> str:
    if day_index == 0:
        return DEFAULT_ARRIVAL_BASE
    candidates = [normalize_andaman_island(v) for v in (selected_destinations or []) if str(v).strip()]
    candidates = [v for v in candidates if v not in {"Port Blair", "Departure"}]
    if candidates:
        return candidates[min(day_index - 1, len(candidates) - 1)]
    return DEFAULT_INTERMEDIATE_REGION
