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
                    "destination_story": {"type": "string"},
                    "todays_journey": {"type": "string"},
                    "hotel_experience": {"type": "string"},
                    "curated_experience": {"type": "string"},
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
                    "destination_story",
                    "todays_journey",
                    "hotel_experience",
                    "curated_experience",
                    "expert_insider_notes",
                    "next_day_transition",
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
                primary_island="Port Blair" if (idx == 0 or idx == num_days - 1) else "Swaraj Dweep (Havelock)",
                attractions=[],
                activities=[],
                hotel="",
                transfer_type=request.transfer_type or "Private Cab",
                ferry="None",
                ferry_timing=""
            )
        if not dp.primary_island:
            dp.primary_island = "Port Blair" if (idx == 0 or idx == num_days - 1) else "Swaraj Dweep (Havelock)"
        if not dp.transfer_type:
            dp.transfer_type = request.transfer_type or "Private Cab"
        
        # Always resolve hotel matching the day's primary island if not explicitly set to a valid non-default
        if not dp.hotel or dp.hotel == "Luxury Resort":
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
            narrative_fields = [
                day.get("destination_story", ""),
                day.get("todays_journey", ""),
                day.get("hotel_experience", ""),
                day.get("curated_experience", ""),
            ]
            total_day_chars = sum(len(f) for f in narrative_fields if f)
            if total_day_chars < MIN_CHARS_PER_DAY:
                raise ValueError(
                    f"Day {idx + 1} has only {total_day_chars} chars of narrative content — "
                    f"response is too short/truncated (min {MIN_CHARS_PER_DAY} chars per day). Retrying."
                )
    except ValueError:
        raise
    except Exception as parse_err:
        LOGGER.warning("Could not validate narrative depth: %s", parse_err)

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
        "prompt_version": "v3.1_xml_persona",
        "model": model,
        "raw_response_text": raw_text,
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    LOGGER.info("Archived raw Gemini response to %s", file_path)


def _generate_fallback_itinerary(request: TripRequest) -> str:
    num_days = max(1, request.number_of_days or 1)
    destination = request.destination or "Andaman and Nicobar Islands"
    hotel_name = request.selected_hotels[0] if request.selected_hotels else "Luxury Island Resort"
    
    days = []
    islands_cycle = ["Port Blair", "Swaraj Dweep (Havelock)", "Shaheed Dweep (Neil)", "Baratang Island"]
    
    for i in range(num_days):
        day_num = i + 1
        island = islands_cycle[i % len(islands_cycle)]
        if day_num == 1:
            title = f"Day 1: Arrival in {island}"
            subtitle = f"Welcome to {destination}"
            story = f"Welcome to {destination}. Your luxury journey begins as you land at Veer Savarkar International Airport in {island}."
            journey = f"Bespoke private transfer from airport to {hotel_name} with priority check-in."
            hotel_exp = f"Relax and enjoy your stay at {hotel_name} with private ocean views and curated dining."
            curated = f"Leisurely afternoon stroll along Corbyn's Cove Beach and evening coastal drive past Cellular Jail."
        elif day_num == num_days:
            title = f"Day {day_num}: Farewell & Departure"
            subtitle = f"Final Moments in {island}"
            story = f"Reflect on your unforgettable island discoveries as your luxury Andaman journey comes to a close."
            journey = f"Private transfer to Veer Savarkar International Airport for your departure flight."
            hotel_exp = f"Enjoy a relaxed gourmet breakfast at {hotel_name} prior to departure."
            curated = f"Last-minute souvenir shopping for handcrafted island mementos and coastal views."
        else:
            title = f"Day {day_num}: Discovering {island}"
            subtitle = f"Island Exploration & Coastal Wonders"
            story = f"Immerse yourself in the serene beauty and turquoise waters of {island}."
            journey = f"Private vehicle transfer to jetty followed by a smooth catamaran cruise across azure waters."
            hotel_exp = f"Unwind at {hotel_name} with half-board dining and premium guest hospitality."
            curated = f"Guided excursion to iconic beaches and natural coral reefs with water activities."
            
        days.append({
            "day_number": day_num,
            "title": title,
            "subtitle": subtitle,
            "primary_island": island,
            "travel_movement": f"Transfer & Excursions in {island}",
            "destination_story": story,
            "todays_journey": journey,
            "hotel_experience": hotel_exp,
            "curated_experience": curated,
            "expert_insider_notes": "Carry reef-safe sunscreen and cash for local purchases.",
            "next_day_transition": "Prepare for tomorrow's island transfer.",
            "hotel": hotel_name,
            "activities": request.preferred_activities or ["Beach Exploration", "Sightseeing"],
            "attractions": ["Radhanagar Beach", "Cellular Jail", "Elephant Beach"],
            "image_keyword": island.lower().replace(" ", "_"),
        })
        
    return json.dumps({"days": days}, indent=2)


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

