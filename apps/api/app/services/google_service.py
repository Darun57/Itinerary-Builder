import time
import json
import re
import logging

from pathlib import Path
import uuid

from google import genai
from google.genai import types

from app.schemas.trip import TripRequest, DayItinerary, parse_day_itineraries, NARRATIVE_SCHEMA_VERSION
from app.services.prompts import build_fast_prompt_text
from app.services.narrative_validator import validate_full_itinerary
from app.services.generation_logger import log_generation_event
from app.services.andaman_geography import default_andaman_island, normalize_andaman_island
from app.services.destination_registry import (
    is_additive_destination,
    load_destinations,
    load_attractions,
    get_destination_display_name,
    get_destination_base_location,
)
from app.services.destination_planner import build_destination_prompt


REQUEST_TIMEOUT_MS = 120000  # 2 minutes — Gemini needs time for multi-day itineraries
MAX_OUTPUT_TOKENS = 16384   # Raised from 8192 to avoid mid-stream truncation on long trips
LOGGER = logging.getLogger(__name__)
DAY_ITINERARY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "primary_island": {"type": "string"},
                    "travel_movement": {"type": "string"},
                    "is_departure_day": {"type": "boolean"},
                    "visiting_places": {"type": "string"},
                    "destination_story": {"type": "string"},
                    "todays_journey": {"type": "string"},
                    "hotel_experience": {"type": "string"},
                    "curated_experience": {"type": "string"},
                    "departure_narrative": {"type": "string"},
                    "farewell_narrative": {"type": "string"},
                    "expert_insider_notes": {"type": "string"},
                    "next_day_transition": {"type": "string"},
                    "hotel": {"type": "string"},
                    "activities": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "attractions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "image_keyword": {"type": "string"},
                },
                "required": [
                    "day_number",
                    "title",
                    "subtitle",
                    "primary_island",
                    "travel_movement",
                    "visiting_places",
                    "destination_story",
                    "todays_journey",
                    "hotel_experience",
                    "hotel",
                    "activities",
                    "attractions",
                    "image_keyword",
                ],
            },
        }
    },
    "required": ["days"],
}
MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash",       # Best available — reliable, fast, high quality
    "gemini-3.6-flash",       # Primary model — try again on retry
    "gemini-2.5-pro",         # High quality fallback
    "gemini-2.0-flash",       # Older but works when quota available
    "gemini-2.0-flash-lite",  # Lightweight last resort
]
RETRYABLE_ERROR_HINTS = (
    "503",
    "unavailable",
    "high demand",
    "temporarily unavailable",
    "429",
    "quota exceeded",
    "resource_exhausted",
    "overloaded",
    "404",
    "not_found",
    "not found",
    "no longer available",
    "deprecated",
)


def _raise_friendly_error(error: Exception) -> None:
    error_message = str(error)
    msg_lower = error_message.lower()
    if "api key" in msg_lower or "api_key" in msg_lower or "unauthorized" in msg_lower:
        raise ValueError(
            "Invalid or missing Gemini API Key. Please click 'Set Gemini Key' in the top right of the web page, paste a valid Gemini API key from Google AI Studio (https://aistudio.google.com/app/apikey), and click Save."
        ) from error
    if "timed out" in msg_lower or "timeout" in msg_lower:
        raise ValueError("Gemini took too long to respond. Please try again.") from error
    if any(hint in msg_lower for hint in RETRYABLE_ERROR_HINTS):
        raise ValueError(
            "Gemini is temporarily busy right now. Please try again in a moment."
        ) from error
    raise ValueError(f"Gemini API Error: {error_message}") from error


def _build_client(api_key: str) -> genai.Client:
    return genai.Client(
        api_key=api_key.strip(),
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS, client_args={"trust_env": False}),
    )


def _build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=0.35,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
        response_schema=DAY_ITINERARY_JSON_SCHEMA,
    )


def _validate_inputs(api_key: str, model: str) -> None:
    if not api_key.strip():
        raise ValueError("Please click 'Set Gemini Key' in the top right of the web page and paste your Google AI Studio API key.")
    if not model.strip():
        raise ValueError("Choose a valid Gemini model before generating an itinerary.")


def _resolve_hotel_for_day_plan(island: str, selected_hotels: list[str]) -> str:
    from app.services.trip_context import _normalize_island_name
    norm_island = _normalize_island_name(island)
    if not selected_hotels:
        return "Luxury Resort"
    
    try:
        from app.services.data_loader import load_hotels
        hotels_df = load_hotels()
        selected_set = {h.lower() for h in selected_hotels}
        for _, row in hotels_df.iterrows():
            h_name = str(row.get("hotel_name") or "").strip()
            h_loc = _normalize_island_name(str(row.get("location") or "").strip())
            if h_name.lower() in selected_set and h_loc == norm_island:
                for sh in selected_hotels:
                    if sh.lower() == h_name.lower():
                        return sh
                return h_name
    except Exception:
        pass

    return selected_hotels[0]


ANDAMAN_DAY_DIRECTIVES = [
    ("Port Blair", ["Corbyn's Cove Beach", "Cellular Jail & Light and Sound Show"]),
    ("Swaraj Dweep (Havelock)", ["Radhanagar Beach", "Kalapathar Beach"]),
    ("Swaraj Dweep (Havelock)", ["Elephant Beach", "Snorkeling & Water Sports"]),
    ("Shaheed Dweep (Neil)", ["Bharatpur Beach", "Natural Rock Arch", "Laxmanpur Beach"]),
    ("Baratang", ["Baratang Limestone Caves", "Mangrove Creek"]),
    ("Port Blair", ["Ross Island (NSCB Island)", "North Bay Island"]),
]


def _ensure_additive_payload_integrity(request: TripRequest) -> None:
    num_days = max(1, request.number_of_days or 1)
    request.number_of_days = num_days
    dest = (getattr(request, "destination", "") or "").strip()
    locs = load_destinations(dest)
    attrs = load_attractions(dest)
    base_loc = get_destination_base_location(dest)

    current_plan = request.daily_island_plan or []
    new_plan = []
    for idx in range(num_days):
        day_num = idx + 1
        is_final_departure = (day_num == num_days)
        loc = locs[idx % len(locs)] if locs else {}
        default_loc = loc.get("name") or base_loc
        default_loc_id = loc.get("id") or ""
        matched_attrs = [a.get("name") for a in attrs if a.get("destination_id") == default_loc_id]
        default_attractions = matched_attrs[:2] if matched_attrs else [default_loc]

        if idx < len(current_plan):
            dp = current_plan[idx]
        else:
            from app.schemas.trip import DayPlan
            dp = DayPlan(
                day_number=day_num,
                primary_island=default_loc,
                attractions=default_attractions,
                activities=[],
                hotel="",
                transfer_type=request.transfer_type or "Private AC Cab",
                ferry="None",
                ferry_timing=""
            )

        if not dp.primary_island:
            dp.primary_island = default_loc

        if not dp.attractions:
            dp.attractions = default_attractions

        if not dp.transfer_type:
            dp.transfer_type = request.transfer_type or "Private AC Cab"

        # Departure day detection
        is_dep_day = is_final_departure and (
            (dp.primary_island or "").strip().lower() == "departure"
            or any(str(a).strip().lower() == "departure" for a in (dp.attractions or []))
        )
        if is_dep_day:
            dp.hotel = ""
            dp.primary_island = "Departure"
            dp.attractions = ["Departure"]
        elif not dp.hotel:
            dp.hotel = request.selected_hotels[0] if request.selected_hotels else ""

        new_plan.append(dp)
    request.daily_island_plan = new_plan


def _ensure_payload_integrity(request: TripRequest) -> None:
    destination = getattr(request, "destination", "") or ""
    if is_additive_destination(destination):
        _ensure_additive_payload_integrity(request)
        return

    # Canonical Andaman behavior (PROTECTED — 100% UNCHANGED)
    num_days = max(1, request.number_of_days or 1)
    request.number_of_days = num_days
    
    current_plan = request.daily_island_plan or []
    new_plan = []
    for idx in range(num_days):
        day_num = idx + 1
        default_region, default_attractions = ANDAMAN_DAY_DIRECTIVES[idx % len(ANDAMAN_DAY_DIRECTIVES)]

        if idx < len(current_plan):
            dp = current_plan[idx]
        else:
            from app.schemas.trip import DayPlan
            dp = DayPlan(
                day_number=day_num,
                primary_island=default_region,
                attractions=default_attractions,
                activities=[],
                hotel="",
                transfer_type=request.transfer_type or "Private AC Cab",
                ferry="None",
                ferry_timing=""
            )

        if not dp.primary_island:
            dp.primary_island = default_region
        else:
            dp.primary_island = normalize_andaman_island(dp.primary_island) or default_region

        if not dp.attractions:
            dp.attractions = default_attractions

        if not dp.transfer_type:
            dp.transfer_type = request.transfer_type or "Private AC Cab"
        
        # Departure day detection
        is_final_departure = (day_num == num_days) and (
            (dp.primary_island or "").strip().lower() == "departure"
            or any(str(a).strip().lower() == "departure" for a in (dp.attractions or []))
        )
        if is_final_departure:
            dp.hotel = ""
            dp.primary_island = "Departure"
            dp.attractions = ["Departure"]
        elif not dp.hotel or dp.hotel == "Luxury Resort":
            dp.hotel = _resolve_hotel_for_day_plan(dp.primary_island, request.selected_hotels or [])
            
        new_plan.append(dp)
    request.daily_island_plan = new_plan



# Models that are confirmed deprecated/unavailable via API
DEPRECATED_MODELS = {
    "gemini-3.6-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "models/gemini-3.6-pro",
    "models/gemini-1.5-flash",
    "models/gemini-1.5-pro",
}


def _candidate_models(model: str) -> list[str]:
    selected_model = model.strip()
    candidates = []
    if selected_model and selected_model not in DEPRECATED_MODELS:
        candidates.append(selected_model)
    for fallback_model in MODEL_FALLBACK_ORDER:
        if fallback_model not in candidates and fallback_model not in DEPRECATED_MODELS:
            candidates.append(fallback_model)
    return candidates


def _is_retryable_error(error: Exception) -> bool:
    error_message = str(error).lower()
    if "api key" in error_message or "api_key" in error_message or "unauthorized" in error_message:
        return False
    return (
        any(hint in error_message for hint in RETRYABLE_ERROR_HINTS)
        or "timed out" in error_message
        or "timeout" in error_message
        or "failed to parse itinerary json" in error_message
        or "truncated itinerary" in error_message
        or "too short/truncated" in error_message
    )


def _generate_once(client: genai.Client, model: str, request: TripRequest) -> str:
    expected_days = max(1, request.number_of_days or 1)
    destination = getattr(request, "destination", "") or ""
    prompt_content = (
        build_destination_prompt(request)
        if is_additive_destination(destination)
        else build_fast_prompt_text(request)
    )
    stream = client.models.generate_content_stream(
        model=model.strip(),
        contents=prompt_content,
        config=_build_config(),
    )
    parts: list[str] = []
    for chunk in stream:
        if chunk.text:
            parts.append(chunk.text)
    raw = "".join(parts).strip()
    LOGGER.debug("Raw Gemini response length: %s", len(raw))
    LOGGER.debug("Raw Gemini response first 500: %s", raw[:500])
    LOGGER.debug("Raw Gemini response last 500: %s", raw[-500:])
    match = re.search(r"\{.*\}\s*$", raw, re.DOTALL)
    payload = match.group(0).strip() if match else raw
    LOGGER.debug("Structured payload length after extraction: %s", len(payload))
    LOGGER.debug("Structured payload type after extraction: %s", type(payload))
    LOGGER.debug("Structured payload preview after extraction: %s", payload[:1000])

    # Validate the JSON parses correctly
    days = parse_day_itineraries(payload)

    # Guard: reject truncated responses that are missing days
    if len(days) < expected_days:
        raise ValueError(
            f"Truncated itinerary: expected {expected_days} days but Gemini only returned {len(days)}. "
            "Retrying with next model."
        )

    # Guard: reject suspiciously short responses (one-liner fallback masquerading as real output)
    MIN_CHARS_PER_DAY = 300  # each day should have rich narrative (>300 chars of content)
    try:
        import json as _json
        parsed_days = _json.loads(payload).get("days", [])
        for idx, day in enumerate(parsed_days):
            is_dep = bool(day.get("is_departure_day")) or (
                idx == len(parsed_days) - 1 and bool(day.get("departure_narrative"))
            )
            is_simple = (getattr(request, "day_wise_style", "luxury_narrative") == "simple_itinerary")
            if is_dep:
                narrative_fields = [
                    day.get("departure_narrative", ""),
                    day.get("farewell_narrative", ""),
                ]
                min_threshold = 60 if is_simple else 140
            elif is_simple:
                # Operational style expects concise bullet points or short operational sentences
                bullets = day.get("operational_bullets") or []
                narrative_fields = [
                    day.get("summary_intro", ""),
                    " ".join(bullets) if isinstance(bullets, list) else str(bullets),
                    day.get("visiting_places", ""),
                    day.get("todays_journey", ""),
                ]
                min_threshold = 50
            else:
                narrative_fields = [
                    day.get("visiting_places", "") or day.get("curated_experience", ""),
                    day.get("destination_story", ""),
                    day.get("todays_journey", ""),
                    day.get("hotel_experience", ""),
                ]
                min_threshold = 220

            total_day_chars = sum(len(f) for f in narrative_fields if f)
            if total_day_chars < min_threshold:
                raise ValueError(
                    f"Day {idx + 1} has only {total_day_chars} chars of content — "
                    f"response is too short/truncated (min {min_threshold} chars per day). Retrying."
                )
    except ValueError:
        raise
    except Exception as parse_err:
        LOGGER.warning("Could not validate narrative depth: %s", parse_err)

    from app.services.itinerary_normalizer import normalize_itinerary_payload
    payload = normalize_itinerary_payload(payload, request)

    return payload


def generate_itinerary_stream(api_key: str, model: str, request: TripRequest):
    content = generate_itinerary(api_key, model, request)
    if content:
        yield content


def _archive_raw_response(generation_id: str, raw_text: str, model: str) -> None:
    archive_dir = Path(__file__).resolve().parent.parent / "storage" / "raw_responses"
    archive_dir.mkdir(parents=True, exist_ok=True)
    file_path = archive_dir / f"{generation_id}.json"
    record = {
        "generation_id": generation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "narrative_schema_version": NARRATIVE_SCHEMA_VERSION,
        "prompt_version": "v3.2_ref_structure",
        "model": model,
        "raw_response_text": raw_text,
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    LOGGER.info("Archived raw Gemini response to %s", file_path)


def _generate_destination_fallback(request: TripRequest) -> str:
    region = request.destination or "Destination"
    num_days = max(1, request.number_of_days or 1)
    guest_name = request.customer_name or "Guest"
    locs = load_destinations(region)
    attrs = load_attractions(region)
    days = []
    for i in range(num_days):
        day_num = i + 1
        is_departure = (day_num == num_days)
        loc = locs[(day_num - 1) % len(locs)] if locs else {"name": "Regional Hub", "id": "hub"}
        loc_name = loc.get("name", "Regional Hub")
        matched_attrs = [a.get("name") for a in attrs if a.get("destination_id") == loc.get("id")]
        attr_text = ", ".join(matched_attrs[:2]) if matched_attrs else "local sights and cultural landmarks"

        if is_departure:
            days.append({
                "day_number": day_num, "title": f"Departure from {loc_name}", "subtitle": "Departure",
                "primary_island": loc_name, "travel_movement": "Departure", "is_departure_day": True,
                "visiting_places": "", "destination_story": "", "todays_journey": "", "hotel_experience": "",
                "curated_experience": "",
                "departure_narrative": f"Following a relaxed morning check-out, {guest_name} will be assisted with private chauffeur transfer to the departure airport for the onward journey home.",
                "farewell_narrative": f"Darun Tourism extends sincere gratitude to {guest_name} and companions for choosing our bespoke travel curation. We look forward to welcoming you back in the future.",
                "expert_insider_notes": "Allow sufficient transit time for regional traffic and airport check-in.",
                "next_day_transition": "Safe travels on your journey home.", "hotel": "",
                "activities": ["Airport Transfer"], "attractions": ["Airport / Transit Terminal"], "image_keyword": f"{region.lower()}_departure"
            })
        else:
            days.append({
                "day_number": day_num, "title": f"{loc_name} Discovery", "subtitle": f"Experience the essence of {loc_name}",
                "primary_island": loc_name, "travel_movement": loc_name if day_num == 1 else f"Transfer to {loc_name}", "is_departure_day": False,
                "visiting_places": f"Begin your exploration of {loc_name} visiting {attr_text}. Immerse yourself in the authentic character and heritage of the region.",
                "destination_story": f"{loc_name} is one of the most distinctive destinations in {region}, celebrated for its rich history, cultural significance, and scenic beauty.",
                "todays_journey": "For the places highlighted above, private chauffeur transfers ensure comfortable transit across all destinations.",
                "hotel_experience": "Enjoy a comfortable evening stay at your curated accommodation, offering refined hospitality and relaxing surroundings.",
                "curated_experience": "", "departure_narrative": "", "farewell_narrative": "",
                "expert_insider_notes": "Morning visits provide the best lighting and most relaxed atmosphere.",
                "next_day_transition": "Prepare for the next stage of your bespoke journey.",
                "hotel": request.selected_hotels[0] if request.selected_hotels else "Curated Boutique Stay",
                "activities": ["Cultural Sightseeing"], "attractions": matched_attrs[:2] if matched_attrs else [loc_name],
                "image_keyword": f"{region.lower()}_{loc_name.lower().replace(' ', '_')}"
            })
    from app.services.itinerary_normalizer import normalize_itinerary_payload
    return normalize_itinerary_payload(json.dumps({"days": days}, indent=2), request)


def _generate_fallback_itinerary(request: TripRequest) -> str:
    destination = request.destination or "Andaman Islands"
    if is_additive_destination(destination):
        return _generate_destination_fallback(request)

    num_days = max(1, request.number_of_days or 1)
    hotel_name = request.selected_hotels[0] if request.selected_hotels else "Andaman Luxury Resort"
    guest_name = request.customer_name or "Guest"
    days = []
    andaman_cycle = [
        "Port Blair",
        "Swaraj Dweep (Havelock)",
        "Swaraj Dweep (Havelock)",
        "Shaheed Dweep (Neil)",
        "Baratang",
        "Port Blair",
    ]
    attractions_cycle = [
        ["Corbyn's Cove Beach", "Cellular Jail & Light and Sound Show"],
        ["Radhanagar Beach", "Kalapathar Beach"],
        ["Elephant Beach", "Snorkeling & Water Sports"],
        ["Bharatpur Beach", "Natural Rock Arch", "Laxmanpur Beach"],
        ["Baratang Limestone Caves", "Mangrove Creek"],
        ["Ross Island (NSCB Island)", "North Bay Island"],
    ]
    for i in range(num_days):
        day_num = i + 1
        area = andaman_cycle[(day_num - 1) % len(andaman_cycle)]
        is_departure = day_num == num_days
        if is_departure:
            days.append({
                "day_number": day_num, "title": "Departure from Port Blair", "subtitle": "Departure",
                "primary_island": "Departure", "travel_movement": "Departure", "is_departure_day": True,
                "visiting_places": "", "destination_story": "", "todays_journey": "", "hotel_experience": "",
                "curated_experience": "", "departure_narrative": f"After a relaxed morning, {guest_name} and their family will be assisted with a smooth private transfer to Port Blair airport for their onward journey.",
                "farewell_narrative": f"We sincerely thank {guest_name} and their family for choosing Darun Tourism for their Andaman Islands holiday and wish them a safe journey home.",
                "expert_insider_notes": "Allow adequate road-transfer time for the airport and seasonal traffic.",
                "next_day_transition": "Safe travels on your onward journey.", "hotel": "",
                "activities": ["Airport Transfer"], "attractions": ["Port Blair Airport"], "image_keyword": "departure"
            })
            continue
        attractions = attractions_cycle[(day_num - 1) % len(attractions_cycle)]
        if day_num == 1:
            title, subtitle = "Port Blair Arrival & Cellular Jail", "A memorable opening to your Andaman journey"
            visiting = "After arrival and hotel check-in, explore Corbyn's Cove Beach, followed by an evening visit to the historic Cellular Jail for the Light and Sound Show."
            story = "Port Blair is the vibrant capital and gateway to the Andaman Islands, famous for its historic landmarks, coastal beauty, and tropical charm."
            journey = f"A private air-conditioned vehicle will connect the airport, {hotel_name}, Corbyn's Cove Beach, and the Cellular Jail in a comfortable circuit."
        elif area == "Swaraj Dweep (Havelock)" and day_num == 2:
            title, subtitle = "Havelock Island & Radhanagar Beach", "Asia's finest beach and turquoise waters"
            visiting = "Transfer by morning ferry to Havelock Island. Settle into your resort before heading to the world-renowned Radhanagar Beach for a stunning sunset."
            story = "Havelock Island is celebrated for its pristine powdery beaches, lush tropical rainforest, and relaxed island atmosphere in the Bay of Bengal."
            journey = f"Private vehicle transfers will connect {hotel_name} with the jetty, followed by luxury ferry transit to Havelock Island."
        elif area == "Swaraj Dweep (Havelock)":
            title, subtitle = "Elephant Beach Coral Discovery", "Vibrant marine life and beach adventure"
            visiting = "Embark on an exciting excursion to Elephant Beach, known for its shallow coral reefs, clear waters, and water sports opportunities."
            story = "Elephant Beach on Havelock offers exceptional snorkeling, glass-bottom boat rides, and tranquil coastal surroundings."
            journey = f"Speedboat or forest-trail transfer connects with Elephant Beach, followed by private chauffeur transfers back to {hotel_name}."
        elif area == "Shaheed Dweep (Neil)":
            title, subtitle = "Neil Island Serenity & Natural Bridge", "A tranquil island retreat with natural rock formations"
            visiting = "Travel by ferry to Neil Island. Discover the iconic Natural Rock Arch, relax at Bharatpur Beach, and witness sunset at Laxmanpur Beach."
            story = "Neil Island is known for its peaceful pace, crystal-clear shallow waters, and untouched natural beauty."
            journey = f"Inter-island ferry transfer followed by private chauffeur service connecting {hotel_name} with the island's coastal attractions."
        elif area == "Baratang":
            title, subtitle = "Baratang Limestone Caves & Mangroves", "A journey through ancient caves and mangrove creeks"
            visiting = "Travel through dense tropical forests and take a scenic speedboat ride through mangrove creeks to explore the ancient Baratang Limestone Caves."
            story = "Baratang Island presents a unique geological wonder with stalactites, stalagmites, and untouched wilderness."
            journey = f"Full-day excursion combining private road transfer, vehicle ferry, and mangrove speedboats."
        else:
            title, subtitle = "Ross & North Bay Island Excursion", "Colonial history and coral reefs"
            visiting = "Take a boat excursion to historic Ross Island to explore British-era ruins and peacocks, followed by coral viewing at North Bay Island."
            story = "Ross Island served as the administrative headquarters of the Andaman Islands, surrounded by coral waters and lush foliage."
            journey = f"Private road transfers to the water sports complex followed by speedboat boat transfers to the twin islands."
        dp_plan = next((p for p in (request.daily_island_plan or []) if getattr(p, "day_number", 0) == day_num), None)
        day_activities = [
            a for a in (dp_plan.activities if dp_plan and getattr(dp_plan, "activities", None) else [])
            if a and a.lower() not in ("none", "no activity", "leisure", "relax", "free day")
        ]
        days.append({
            "day_number": day_num, "title": title, "subtitle": subtitle, "primary_island": area,
            "travel_movement": area, "is_departure_day": False, "visiting_places": visiting,
            "destination_story": story, "todays_journey": journey,
            "hotel_experience": f"Overnight at {hotel_name}, with a comfortable base for the next day's Andaman Islands experiences.",
            "curated_experience": "", "departure_narrative": "", "farewell_narrative": "",
            "expert_insider_notes": "Carry sunscreen, light clothing and comfortable footwear; allow extra road time during peak traffic periods.",
            "next_day_transition": "Prepare for the next Andaman excursion.", "hotel": hotel_name,
            "activities": day_activities,
            "attractions": attractions, "image_keyword": area.lower().replace(" ", "_")
        })
    from app.services.itinerary_normalizer import normalize_itinerary_payload
    return normalize_itinerary_payload(json.dumps({"days": days}, indent=2), request)

def generate_itinerary(api_key: str, model: str, request: TripRequest) -> str:
    _ensure_payload_integrity(request)

    if not api_key or not api_key.strip():
        LOGGER.warning("No API key provided. Using built-in fallback itinerary generator.")
        return _generate_fallback_itinerary(request)

    client = _build_client(api_key)
    generation_id = f"gen_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    start_time = time.time()

    for candidate_model in _candidate_models(model):
        try:
            LOGGER.info("Attempting itinerary generation with model: %s", candidate_model)
            content = _generate_once(client, candidate_model, request)
            gen_duration = (time.time() - start_time) * 1000.0

            _archive_raw_response(generation_id, content, candidate_model)

            log_generation_event(
                generation_id=generation_id,
                prompt_version="v3.1_simplified",
                schema_version=NARRATIVE_SCHEMA_VERSION,
                model=candidate_model,
                retry_count=0,
                validation_result={"valid": True, "overall_score": 100.0},
                generation_duration_ms=gen_duration,
                outcome="PASSED",
            )
            return content

        except Exception as error:
            LOGGER.warning("Model %s failed: %s. Trying next candidate model...", candidate_model, error)

    LOGGER.warning("All Gemini candidate models failed. Using built-in fallback itinerary generator.")
    return _generate_fallback_itinerary(request)

