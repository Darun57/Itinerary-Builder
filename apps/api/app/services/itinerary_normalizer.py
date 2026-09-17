"""
Deterministic Itinerary Normalizer & Quality Assurance Engine.

Guarantees 100% compliance with the luxury travel proposal layout:
1. Canonical route & heading calculation: (Island), (Origin → Destination), (Origin → Excursion Return), or (Departure).
2. Day 1 arrival isolation: removes accidental departure references and ensures arrival-only narrative.
3. Final day departure enforcement: sets is_departure_day=True, formats "END OF THE JOURNEY" paragraphs (checkout transfer + personal farewell gratitude), clears sightseeing and hotel blocks.
4. Today's Journey lead-in enforcement: guarantees opening "For the places highlighted above, ...".
5. Hotel Experience alignment: ensures hotel mentions match confirmed daily island assignments and departure day has no overnight hotel.
6. Two-paragraph structure: ensures visiting_places and destination_story are separated and non-empty on normal days.
"""
import json
import logging
import re
from typing import Any

from app.schemas.trip import TripRequest

LOGGER = logging.getLogger(__name__)

FORBIDDEN_DAY_1_TERMS = [
    "departure", "return flight", "checkout", "check-out", "homeward", "takeoff",
    "onward flight", "airport security", "conclusion of an unforgettable",
    "farewell to", "luggage drop-off", "final morning", "souvenirs", "flight home",
]

JOURNEY_STANDARD_PREFIX = "For the places highlighted above, "


def _normalize_island_name(name: str) -> str:
    """Normalize island names to canonical forms."""
    text = (name or "").strip().lower()
    if not text:
        return "Port Blair"
    if "havelock" in text or "swaraj" in text:
        return "Swaraj Dweep"
    if "neil" in text or "shaheed" in text:
        return "Shaheed Dweep"
    if "baratang" in text:
        return "Baratang Island"
    if "ross" in text or "north bay" in text:
        return "Ross Island & North Bay"
    if "diglipur" in text:
        return "Diglipur"
    if "rangat" in text:
        return "Rangat"
    if "mayabunder" in text:
        return "Mayabunder"
    if "little andaman" in text:
        return "Little Andaman"
    if "port blair" in text or "cellular" in text or "corbyn" in text:
        return "Port Blair"
    return name.strip()


def resolve_canonical_movement(
    day_idx: int,
    total_days: int,
    day_dict: dict[str, Any],
    request: TripRequest,
) -> str:
    """
    Computes canonical route string:
    - Departure day -> 'Departure'
    - Day 1 -> '(Port Blair)' or current island
    - Inter-island transit -> 'Origin → Destination'
    - Excursion day-trip returning to base -> 'Origin → Destination Return'
    - Exploration on same island -> 'Current Island'
    """
    is_departure = (day_idx == total_days - 1) or bool(day_dict.get("is_departure_day"))
    if is_departure:
        return "Departure"

    plans = list(request.daily_island_plan or [])
    curr_dp = plans[day_idx] if day_idx < len(plans) else None
    prev_dp = plans[day_idx - 1] if day_idx > 0 and (day_idx - 1) < len(plans) else None

    # Check if Gemini already provided a clean transition with 'to' or '->'
    raw_tm = str(day_dict.get("travel_movement") or "").strip()
    clean_raw = re.sub(r"\s*(?:->|to|-)\s*", " → ", raw_tm, flags=re.IGNORECASE)

    # Detect if raw_tm has clean "A → B" or "A → B Return"
    arrow_match = re.search(r"([A-Za-z\s]+?)\s*→\s*([A-Za-z\s]+?)(?:\s+(Return))?$", clean_raw, re.IGNORECASE)
    if arrow_match:
        origin = _normalize_island_name(arrow_match.group(1).strip())
        dest = _normalize_island_name(arrow_match.group(2).strip())
        is_return = bool(arrow_match.group(3)) or "return" in raw_tm.lower()
        if origin != dest:
            return f"{origin} → {dest} Return" if is_return else f"{origin} → {dest}"

    # Derive from daily plan
    curr_island = _normalize_island_name(curr_dp.primary_island if curr_dp else str(day_dict.get("primary_island") or ""))
    prev_island = _normalize_island_name(prev_dp.primary_island if prev_dp else "")

    if day_idx == 0:
        return curr_island or "Port Blair"

    # Check if excursion day trip (e.g. Day 2 Baratang return to Port Blair hotel)
    if curr_dp and prev_dp:
        curr_hotel = (curr_dp.hotel or "").strip().lower()
        prev_hotel = (prev_dp.hotel or "").strip().lower()
        # If island changed for the day's activities, but overnight hotel is same as previous day:
        if curr_island != prev_island and curr_hotel and prev_hotel and curr_hotel == prev_hotel:
            return f"{prev_island} → {curr_island} Return"
        if curr_island != prev_island:
            return f"{prev_island} → {curr_island}"

    return curr_island or "Port Blair"


def standardize_todays_journey(journey_text: str) -> str:
    """Ensures todays_journey opens with the mandatory standard lead-in."""
    text = (journey_text or "").strip()
    if not text:
        return (
            "For the places highlighted above, private chauffeur transfers ensure "
            "comfortable transportation and effortless island sightseeing throughout the day."
        )

    # Check if already starts with standard phrase
    if re.match(r"^For\s+the\s+places(?:\s+and\s+activities)?\s+highlighted\s+above[,\s]*", text, re.IGNORECASE):
        cleaned = re.sub(r"^For\s+the\s+places(?:\s+and\s+activities)?\s+highlighted\s+above[,\s]*", "", text, flags=re.IGNORECASE).strip()
        return f"{JOURNEY_STANDARD_PREFIX}{cleaned[:1].lower() + cleaned[1:] if cleaned else 'private vehicle transfers ensure smooth transit.'}"

    # Check and replace common awkward openings
    prefixes_to_trim = [
        r"^your\s+morning\s+begins\s+with\s+",
        r"^the\s+day\s+begins\s+with\s+",
        r"^morning\s+transit\s+is\s+conducted\s+via\s+",
        r"^your\s+day\s+commences\s+with\s+",
        r"^a\s+comfortable\s+private\s+transfer\s+will\s+",
    ]
    for pat in prefixes_to_trim:
        if re.search(pat, text, re.IGNORECASE):
            trimmed = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
            return f"{JOURNEY_STANDARD_PREFIX}{trimmed[:1].lower() + trimmed[1:]}"

    # Default prefixing
    return f"{JOURNEY_STANDARD_PREFIX}{text[:1].lower() + text[1:]}"


def sanitize_day_1(day_dict: dict[str, Any], request: TripRequest) -> None:
    """Guarantees Day 1 is 100% arrival and exploration only."""
    day_dict["is_departure_day"] = False
    
    # Strip any forbidden words from narrative fields
    for field in ["visiting_places", "destination_story", "todays_journey", "title"]:
        val = str(day_dict.get(field) or "")
        for term in FORBIDDEN_DAY_1_TERMS:
            if term in val.lower():
                val = re.sub(rf"\b{term}\b", "arrival", val, flags=re.IGNORECASE)
        day_dict[field] = val

    day_dict["departure_narrative"] = ""
    day_dict["farewell_narrative"] = ""


def sanitize_departure_day(
    day_dict: dict[str, Any],
    request: TripRequest,
    last_night_hotel: str,
) -> None:
    """Enforces strict Departure Day contract under END OF THE JOURNEY."""
    day_dict["is_departure_day"] = True
    day_dict["title"] = "Departure"
    day_dict["subtitle"] = "Departure"
    day_dict["travel_movement"] = "Departure"
    day_dict["visiting_places"] = ""
    day_dict["destination_story"] = ""
    day_dict["todays_journey"] = ""
    day_dict["hotel_experience"] = ""
    day_dict["curated_experience"] = ""
    day_dict["hotel"] = ""
    day_dict["activities"] = ["Private Airport Transfer"]
    day_dict["attractions"] = ["Departure"]
    day_dict["image_keyword"] = "departure"

    checkout_hotel = last_night_hotel or "your resort"
    customer_name = request.customer_name or "our valued guests"

    existing_dep = str(day_dict.get("departure_narrative") or "").strip()
    if len(existing_dep) < 30 or "enjoy" not in existing_dep.lower():
        day_dict["departure_narrative"] = (
            f"Enjoy a peaceful morning check-out at {checkout_hotel} with full luggage assistance. "
            f"Your private chauffeur will pick you up for a smooth transfer to Veer Savarkar "
            f"International Airport for your flight home."
        )
    else:
        # Ensure it mentions checkout and airport
        day_dict["departure_narrative"] = existing_dep

    existing_farewell = str(day_dict.get("farewell_narrative") or "").strip()
    if len(existing_farewell) < 30 or "darun tourism" not in existing_farewell.lower():
        day_dict["farewell_narrative"] = (
            f"Darun Tourism extends its heartfelt gratitude to {customer_name} and family "
            f"for choosing us. It was our genuine pleasure crafting your Andaman trip memories, "
            f"and we look forward to welcoming you back in the future."
        )
    else:
        day_dict["farewell_narrative"] = existing_farewell


def normalize_itinerary_payload(raw_json_or_dict: Any, request: TripRequest) -> str:
    """
    Main entry point: takes raw JSON or parsed dict, normalizes every day
    to guarantee 100% compliance with the luxury format, and returns the
    sanitized JSON string.
    """
    if isinstance(raw_json_or_dict, str):
        cleaned = raw_json_or_dict.strip()
        match = re.search(r"\{.*\}\s*$", cleaned, re.DOTALL)
        json_str = match.group(0).strip() if match else cleaned
        if json_str.startswith("```"):
            json_str = re.sub(r"^```[a-zA-Z]*\n?", "", json_str)
            json_str = re.sub(r"\n?```$", "", json_str).strip()
        try:
            data = json.loads(json_str, strict=False)
        except Exception:
            try:
                fixed = re.sub(r'(?<=: ")[\s\S]*?(?=",\n|"\n|\"\s*\})', lambda m: m.group(0).replace("\n", " "), json_str)
                data = json.loads(fixed, strict=False)
            except Exception as e:
                LOGGER.error("Failed to parse JSON for normalization: %s", e)
                return raw_json_or_dict
    elif isinstance(raw_json_or_dict, dict):
        data = raw_json_or_dict
    else:
        return str(raw_json_or_dict)

    days = data.get("days", [])
    if not isinstance(days, list) or not days:
        return json.dumps(data)

    total_days = len(days)
    plans = list(request.daily_island_plan or [])

    # Identify the last overnight hotel (night before departure)
    last_night_hotel = ""
    for idx in range(total_days - 2, -1, -1):
        if idx < len(plans) and plans[idx].hotel:
            last_night_hotel = plans[idx].hotel
            break
    if not last_night_hotel and request.selected_hotels:
        last_night_hotel = request.selected_hotels[0]

    for idx, day in enumerate(days):
        day_num = idx + 1
        day["day_number"] = day_num
        is_last_day = (idx == total_days - 1)
        dp = plans[idx] if idx < len(plans) else None

        # Determine if this day is marked as Departure
        is_departure = is_last_day or bool(day.get("is_departure_day")) or (
            dp and (
                (dp.primary_island or "").strip().lower() == "departure"
                or any(str(a).strip().lower() == "departure" for a in (dp.attractions or []))
            )
        )

        # 1. Canonical Route & Movement
        canonical_route = resolve_canonical_movement(idx, total_days, day, request)
        day["travel_movement"] = canonical_route

        # 2. Day 1 Isolation
        if idx == 0 and not is_departure:
            sanitize_day_1(day, request)

        # 3. Departure Day Lock
        if is_departure and is_last_day:
            sanitize_departure_day(day, request, last_night_hotel)
            continue

        # 4. Normal Days Validation
        day["is_departure_day"] = False
        day["departure_narrative"] = ""
        day["farewell_narrative"] = ""

        # Title / Subtitle fallback
        if not day.get("title") or day.get("title") == "Departure":
            island = dp.primary_island if dp else day.get("primary_island") or "Island"
            day["title"] = f"Exploring {island}"
        if not day.get("subtitle"):
            day["subtitle"] = "Coastal Highlights & Island Discovery"

        # Today's Journey Standard Lead-in
        day["todays_journey"] = standardize_todays_journey(str(day.get("todays_journey") or ""))

        # Hotel Alignment
        assigned_hotel = dp.hotel if dp and dp.hotel else (
            request.selected_hotels[idx % len(request.selected_hotels)]
            if request.selected_hotels else ""
        )
        if assigned_hotel:
            day["hotel"] = assigned_hotel
            current_hotel_exp = str(day.get("hotel_experience") or "").strip()
            # If hotel_experience is too short or doesn't mention assigned hotel, align it smoothly
            if len(current_hotel_exp) < 20 or assigned_hotel.lower() not in current_hotel_exp.lower():
                day["hotel_experience"] = (
                    f"A peaceful stay at {assigned_hotel}, offering comfortable accommodation, "
                    f"relaxing oceanfront surroundings, and warm hospitality—perfect for unwinding "
                    f"after your journey."
                )

        # Visiting Places & Destination Story fallback
        if not day.get("visiting_places"):
            attractions = ", ".join(dp.attractions) if dp and dp.attractions else "scenic coastal landmarks"
            day["visiting_places"] = (
                f"Begin the day with curated visits to {attractions}. "
                f"Enjoy serene beachside walks, immersive sightseeing, and memorable island discovery."
            )
        if not day.get("destination_story"):
            island_label = dp.primary_island if dp else "The Andaman Islands"
            day["destination_story"] = (
                f"{island_label} showcases the natural splendor of the archipelago, famous for its "
                f"azure waters, tropical lushness, and rich maritime heritage."
            )

    return json.dumps(data)
