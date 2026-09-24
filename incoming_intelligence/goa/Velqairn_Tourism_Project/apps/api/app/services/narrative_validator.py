"""
Narrative Intelligence Layered Validation Engine (Schema, Quality Scoring, Consistency).

Schema Version: v2.0
"""
import json
import logging
import re
from typing import Any

from app.schemas.trip import TripRequest

LOGGER = logging.getLogger(__name__)

REQUIRED_NORMAL_FIELDS = [
    "destination_story",
    "todays_journey",
    "hotel_experience",
]

GENERIC_PLACEHOLDERS = [
    "the morning opens",
    "the afternoon continues",
    "the evening is reserved",
    "enjoy sightseeing",
    "relax and unwind",
    "guest comfort",
    "polished close",
    "wind down",
    "comfortable overnight stay",
    "smooth start",
]


def validate_schema(day_dict: dict[str, Any]) -> tuple[bool, list[str]]:
    """Stage 1: Verify presence and type of required narrative fields."""
    errors = []
    is_departure = bool(day_dict.get("is_departure_day"))

    if is_departure:
        # Departure Day
        has_dep = bool(str(day_dict.get("departure_narrative") or day_dict.get("todays_journey") or "").strip())
        has_farewell = bool(str(day_dict.get("farewell_narrative") or day_dict.get("destination_story") or "").strip())
        if not has_dep:
            errors.append("Missing or empty required field for departure day: departure_narrative")
        if not has_farewell:
            errors.append("Missing or empty required field for departure day: farewell_narrative")
    else:
        # Normal Day
        has_visiting = bool(str(day_dict.get("visiting_places") or day_dict.get("curated_experience") or "").strip())
        if not has_visiting:
            errors.append("Missing or empty required field: visiting_places")
        for field_name in REQUIRED_NORMAL_FIELDS:
            val = day_dict.get(field_name)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"Missing or empty required field: {field_name}")

    return (len(errors) == 0, errors)


def evaluate_quality_score(day_dict: dict[str, Any], request: TripRequest) -> tuple[float, dict[str, float], list[str]]:
    """
    Stage 2: Weighted Quality Scoring Engine (0 - 100 Scale).
    Returns (overall_score, section_scores, failed_rules).
    """
    failed_rules = []
    section_scores: dict[str, float] = {}

    destination = (request.destination or "Goa").lower()
    selected_hotels = [h.lower() for h in (request.selected_hotels or [])]
    is_departure = bool(day_dict.get("is_departure_day"))

    if is_departure:
        dep_text = str(day_dict.get("departure_narrative") or day_dict.get("todays_journey") or "").strip()
        score_dep = 100.0
        if len(dep_text.split()) < 20:
            score_dep -= 30
            failed_rules.append("Departure narrative too short (<20 words)")
        if any(p in dep_text.lower() for p in GENERIC_PLACEHOLDERS):
            score_dep -= 30
            failed_rules.append("Departure narrative contains generic placeholder text")
        section_scores["departure_narrative"] = max(0.0, score_dep)

        farewell_text = str(day_dict.get("farewell_narrative") or day_dict.get("destination_story") or "").strip()
        score_farewell = 100.0
        if len(farewell_text.split()) < 20:
            score_farewell -= 30
            failed_rules.append("Farewell narrative too short (<20 words)")
        if any(p in farewell_text.lower() for p in GENERIC_PLACEHOLDERS):
            score_farewell -= 30
            failed_rules.append("Farewell narrative contains generic placeholder text")
        section_scores["farewell_narrative"] = max(0.0, score_farewell)

        overall_score = (score_dep + score_farewell) / 2.0
        return (overall_score, section_scores, failed_rules)

    # 1. Visiting Places (Weight: 25%)
    visiting = str(day_dict.get("visiting_places") or day_dict.get("curated_experience") or "").strip()
    score_visiting = 100.0
    if len(visiting.split()) < 20:
        score_visiting -= 30
        failed_rules.append("Visiting places description too short (<20 words)")
    if any(p in visiting.lower() for p in GENERIC_PLACEHOLDERS):
        score_visiting -= 30
        failed_rules.append("Visiting places contains generic placeholder text")
    section_scores["visiting_places"] = max(0.0, score_visiting)

    # 2. Destination Story (Weight: 25%)
    story = str(day_dict.get("destination_story") or "").strip()
    words_story = len(story.split())
    score_story = 100.0
    if words_story < 20:
        score_story -= 30
        failed_rules.append("Destination story too short (<20 words)")
    if any(p in story.lower() for p in GENERIC_PLACEHOLDERS):
        score_story -= 30
        failed_rules.append("Destination story contains generic placeholder text")
    section_scores["destination_story"] = max(0.0, score_story)

    # 3. Today's Journey (Weight: 25%)
    journey = str(day_dict.get("todays_journey") or "").strip()
    score_journey = 100.0
    if len(journey.split()) < 15:
        score_journey -= 30
        failed_rules.append("Today's journey description too short (<15 words)")
    if any(p in journey.lower() for p in GENERIC_PLACEHOLDERS):
        score_journey -= 30
        failed_rules.append("Today's journey contains generic placeholder text")
    section_scores["todays_journey"] = max(0.0, score_journey)

    # 4. Hotel Experience (Weight: 25%)
    hotel_exp = str(day_dict.get("hotel_experience") or "").strip()
    score_hotel = 100.0
    if len(hotel_exp.split()) < 15:
        score_hotel -= 30
        failed_rules.append("Hotel experience description too short (<15 words)")
    if selected_hotels and not any(h in hotel_exp.lower() for h in selected_hotels):
        score_hotel -= 25
        failed_rules.append("Hotel experience does not reference any mandatory selected hotel")
    section_scores["hotel_experience"] = max(0.0, score_hotel)

    overall_score = (score_visiting * 0.25 + score_story * 0.25 + score_journey * 0.25 + score_hotel * 0.25)
    return (overall_score, section_scores, failed_rules)


def validate_consistency(days: list[dict[str, Any]], request: TripRequest) -> tuple[bool, list[str]]:
    """
    Stage 3: Cross-Day Consistency & Timeline Logic Validator.
    Checks sequence, regional transport matching, and arrival/departure rules.
    """
    errors = []
    total_days = len(days)

    if total_days != request.number_of_days:
        errors.append(f"Day count mismatch: Expected {request.number_of_days}, got {total_days}")

    for idx, day in enumerate(days):
        day_num = idx + 1
        title = str(day.get("title") or "").lower()
        story = str(day.get("destination_story") or "").lower()
        journey = str(day.get("todays_journey") or "").lower()

        # Day 1 Arrival Isolation
        if day_num == 1:
            day_1_combined = " ".join([
                title, story, journey,
                str(day.get("curated_experience") or "").lower(),
                str(day.get("hotel_experience") or "").lower(),
                str(day.get("expert_insider_notes") or "").lower(),
                str(day.get("next_day_transition") or "").lower(),
            ])
            forbidden_day_1_terms = [
                "departure", "return flight", "checkout", "check-out", "homeward", "takeoff",
                "onward flight", "airport security", "conclusion of an unforgettable",
                "farewell to", "luggage drop-off", "final morning", "souvenirs"
            ]
            for term in forbidden_day_1_terms:
                if term in day_1_combined:
                    errors.append(f"Day 1 contains departure/return flight term: '{term}'. Day 1 must be arrival only.")
                    break

        # Regional transport logic check
        if idx > 0:
            prev_island = str(days[idx - 1].get("primary_island") or "").strip().lower()
            curr_island = str(day.get("primary_island") or "").strip().lower()
            if prev_island and curr_island and prev_island != curr_island:
                combined_text = (journey + " " + str(day.get("travel_movement") or "")).lower()
                if "ferry" not in combined_text and "transfer" not in combined_text and "flight" not in combined_text:
                    errors.append(f"Day {day_num} changes region from {prev_island} to {curr_island} but journey mentions no transfer, ferry, or boat movement.")

    return (len(errors) == 0, errors)


def validate_full_itinerary(raw_json: str, request: TripRequest) -> dict[str, Any]:
    """
    Runs the complete 3-stage validation pipeline on Gemini JSON payload.
    Returns diagnostic dict containing overall_score, section_scores, failed_rules, and pass/fail verdict.
    """
    result: dict[str, Any] = {
        "valid": False,
        "overall_score": 0.0,
        "section_scores": {},
        "errors": [],
        "failed_rules": [],
    }

    try:
        cleaned = (raw_json or "").strip()
        match = re.search(r"\{.*\}\s*$", cleaned, re.DOTALL)
        json_candidate = match.group(0).strip() if match else cleaned
        if json_candidate.startswith("```"):
            json_candidate = re.sub(r"^```[a-zA-Z]*\n?", "", json_candidate)
            json_candidate = re.sub(r"\n?```$", "", json_candidate).strip()

        data = json.loads(json_candidate, strict=False)
        days = data.get("days", [])
        if not isinstance(days, list) or not days:
            result["errors"].append("JSON missing valid 'days' array")
            return result

        # Stage 1: Schema Check for every day
        for idx, day in enumerate(days):
            schema_ok, schema_errs = validate_schema(day)
            if not schema_ok:
                result["errors"].extend([f"Day {idx+1}: {e}" for e in schema_errs])

        # Stage 2: Quality Scoring across all days
        day_scores = []
        all_failed_rules = []
        all_section_scores: dict[str, list[float]] = {}

        for idx, day in enumerate(days):
            score, sec_scores, rules = evaluate_quality_score(day, request)
            day_scores.append(score)
            all_failed_rules.extend([f"Day {idx+1}: {r}" for r in rules])
            for k, s in sec_scores.items():
                all_section_scores.setdefault(k, []).append(s)

        avg_overall_score = sum(day_scores) / len(day_scores) if day_scores else 0.0
        avg_section_scores = {k: (sum(v) / len(v) if v else 0.0) for k, v in all_section_scores.items()}

        result["overall_score"] = round(avg_overall_score, 2)
        result["section_scores"] = {k: round(v, 2) for k, v in avg_section_scores.items()}
        result["failed_rules"] = all_failed_rules

        # Stage 3: Consistency Validation
        consistency_ok, consistency_errs = validate_consistency(days, request)
        if not consistency_ok:
            result["errors"].extend(consistency_errs)

        # Passing Threshold: Schema valid, Consistency valid, Overall Score >= 70
        is_passing = (len(result["errors"]) == 0) and (avg_overall_score >= 70.0)
        result["valid"] = is_passing

    except Exception as exc:
        result["errors"].append(f"JSON Parsing Error: {str(exc)}")

    return result
