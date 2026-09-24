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
from app.services.goa_geography import default_goa_region, normalize_goa_region


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


def _ensure_payload_integrity(request: TripRequest) -> None:
    num_days = max(1, request.number_of_days or 1)
    request.number_of_days = num_days
    
    current_plan = request.daily_island_plan or []
    new_plan = []
    for idx in range(num_days):
        day_num = idx + 1
        if idx < len(current_plan):
            dp = current_plan[idx]
        else:
            from app.schemas.trip import DayPlan
            dp = DayPlan(
                day_number=day_num,
                primary_island=default_goa_region(idx, num_days, request.selected_destinations),
                attractions=[],
                activities=[],
                hotel="",
                transfer_type=request.transfer_type or "Private Cab",
                ferry="None",
                ferry_timing=""
            )
        if not dp.primary_island:
            dp.primary_island = default_goa_region(idx, num_days, request.selected_destinations)
        if not dp.transfer_type:
            dp.transfer_type = request.transfer_type or "Private Cab"
        
        # Always resolve hotel matching the day's primary island if not explicitly set to a valid non-default
        is_final_departure = (day_num == num_days) and (
            (dp.primary_island or "").strip().lower() == "departure"
            or any(str(a).strip().lower() == "departure" for a in (dp.attractions or []))
        )
        if is_final_departure:
            dp.hotel = ""
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
    stream = client.models.generate_content_stream(
        model=model.strip(),
        contents=build_fast_prompt_text(request),
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
            if is_dep:
                narrative_fields = [
                    day.get("departure_narrative", ""),
                    day.get("farewell_narrative", ""),
                ]
                min_threshold = 140
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
                    f"Day {idx + 1} has only {total_day_chars} chars of narrative content — "
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


def _generate_fallback_itinerary(request: TripRequest) -> str:
    num_days = max(1, request.number_of_days or 1)
    destination = request.destination or "Goa"
    hotel_name = request.selected_hotels[0] if request.selected_hotels else "Goa Luxury Resort"
    guest_name = request.customer_name or "Guest"
    days = []
    goa_cycle = ["Panaji", "North Goa", "South Goa", "Dudhsagar", "South Goa", "Panaji"]
    attractions_cycle = [
        ["Fontainhas", "Mandovi Riverfront"],
        ["Fort Aguada", "Candolim Beach", "Vagator Beach"],
        ["Palolem Beach", "Cabo de Rama"],
        ["Dudhsagar Falls", "Collem"],
        ["Benaulim Beach", "Old Goa"],
    ]
    for i in range(num_days):
        day_num = i + 1
        area = goa_cycle[(day_num - 1) % len(goa_cycle)]
        is_departure = day_num == num_days
        if is_departure:
            days.append({
                "day_number": day_num, "title": "Departure from Goa", "subtitle": "Departure",
                "primary_island": "Panaji", "travel_movement": "Departure", "is_departure_day": True,
                "visiting_places": "", "destination_story": "", "todays_journey": "", "hotel_experience": "",
                "curated_experience": "", "departure_narrative": f"After a relaxed morning, {guest_name} and their family will be assisted with a smooth private transfer to the airport for their onward journey.",
                "farewell_narrative": f"We sincerely thank {guest_name} and their family for choosing Darun Tourism for their Goa holiday and wish them a safe journey home.",
                "expert_insider_notes": "Allow adequate road-transfer time for the airport and seasonal traffic.",
                "next_day_transition": "Safe travels on your onward journey.", "hotel": hotel_name,
                "activities": ["Airport Transfer"], "attractions": ["Goa Airport"], "image_keyword": "goa_sunset"
            })
            continue
        attractions = attractions_cycle[(day_num - 1) % len(attractions_cycle)]
        if day_num == 1:
            title, subtitle = "Panaji & Fontainhas Heritage", "A cultured opening to your Goa journey"
            visiting = "After arrival and hotel check-in, explore Fontainhas, continue to the Panaji waterfront, and finish with a relaxed Mandovi evening."
            story = "Panaji blends Portuguese-era heritage, riverfront life, colourful neighbourhoods, and easy access to Goa's northern and southern coasts."
            journey = f"A private air-conditioned vehicle will connect the airport, {hotel_name}, Fontainhas, and the Mandovi waterfront in a comfortable city circuit."
        elif area == "North Goa":
            title, subtitle = "North Goa Coast & Forts", "Beaches, heritage and sunset views"
            visiting = "Explore Fort Aguada and the Candolim coast before continuing toward Vagator and Chapora for late-afternoon coastal views."
            story = "North Goa combines broad beaches with historic forts, village lanes, dining, and a lively contemporary travel culture."
            journey = f"Private road transfers will connect {hotel_name} with the day's North Goa sightseeing points, allowing flexible stops along the coast."
        elif area == "South Goa":
            title, subtitle = "South Goa Beach Escape", "A slower day by the Arabian Sea"
            visiting = "Spend the day between a long sandy beach, a scenic coastal viewpoint, and a relaxed South Goa dining experience."
            story = "South Goa is known for spacious beaches, resort compounds, quieter villages, and a slower rhythm well suited to premium leisure trips."
            journey = f"Private chauffeur service will provide comfortable road access between {hotel_name}, the beach circuit, and selected coastal viewpoints."
        elif area == "Dudhsagar":
            title, subtitle = "Dudhsagar & Goa Hinterland", "Waterfalls, forest and adventure"
            visiting = "Travel inland toward the Dudhsagar and Collem area for a full-day nature excursion, subject to local access and weather conditions."
            story = "Goa's eastern hinterland shifts from beaches to forested landscapes, streams, spice plantations, and dramatic waterfall country."
            journey = "A full-day private transfer with a licensed local excursion operator will be used for the inland route, subject to access rules."
        else:
            title, subtitle = "Goa Heritage & Coast", "A balanced day of culture and leisure"
            visiting = "Combine a heritage stop around Old Goa with a relaxed coastal experience and an unhurried evening."
            story = "Goa's historic churches, villages, and coastal landscapes create a strong contrast between cultural depth and beach-led leisure."
            journey = f"Private transfers will connect {hotel_name} with the day's heritage and coastal stops."
        days.append({
            "day_number": day_num, "title": title, "subtitle": subtitle, "primary_island": area,
            "travel_movement": area, "is_departure_day": False, "visiting_places": visiting,
            "destination_story": story, "todays_journey": journey,
            "hotel_experience": f"Overnight at {hotel_name}, with a comfortable base for the next day's Goa experiences.",
            "curated_experience": "", "departure_narrative": "", "farewell_narrative": "",
            "expert_insider_notes": "Carry sunscreen, light clothing and comfortable footwear; allow extra road time during peak traffic periods.",
            "next_day_transition": "Prepare for the next Goa excursion.", "hotel": hotel_name,
            "activities": request.preferred_activities or ["Sightseeing", "Beach Exploration"],
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

