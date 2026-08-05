"""
Narrative Intelligence Layered Validation Engine (Schema, Quality Scoring, Consistency).

Schema Version: v2.0
"""
import json
import logging
from typing import Any

from app.schemas.trip import TripRequest

LOGGER = logging.getLogger(__name__)

REQUIRED_NARRATIVE_FIELDS = [
    "destination_story",
    "todays_journey",
    "curated_experience",
    "hotel_experience",
    "expert_insider_notes",
    "next_day_transition",
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
    for field_name in REQUIRED_NARRATIVE_FIELDS:
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

    destination = (request.destination or "Andaman").lower()
    selected_hotels = [h.lower() for h in (request.selected_hotels or [])]

    # 1. Destination Story (Weight: 20%)
    story = str(day_dict.get("destination_story") or "").strip()
    words_story = len(story.split())
    score_story = 100.0
    if words_story < 25:
        score_story -= 30
        failed_rules.append("Destination story too short (<25 words)")
    if any(p in story.lower() for p in GENERIC_PLACEHOLDERS):
        score_story -= 40
        failed_rules.append("Destination story contains generic placeholder text")
    section_scores["destination_story"] = max(0.0, score_story)

    # 2. Today's Journey (Weight: 15%)
    journey = str(day_dict.get("todays_journey") or "").strip()
    score_journey = 100.0
    if len(journey.split()) < 20:
        score_journey -= 30
        failed_rules.append("Today's journey description too short (<20 words)")
    if any(p in journey.lower() for p in GENERIC_PLACEHOLDERS):
        score_journey -= 30
        failed_rules.append("Today's journey contains generic placeholder text")
    section_scores["todays_journey"] = max(0.0, score_journey)

    # 3. Curated Experience (Weight: 20%)
    experience = str(day_dict.get("curated_experience") or "").strip()
    score_exp = 100.0
    if len(experience.split()) < 25:
        score_exp -= 30
        failed_rules.append("Curated experience description too short (<25 words)")
    if any(p in experience.lower() for p in GENERIC_PLACEHOLDERS):
        score_exp -= 40
        failed_rules.append("Curated experience contains generic placeholder text")
    section_scores["curated_experience"] = max(0.0, score_exp)

    # 4. Hotel Experience (Weight: 20%)
    hotel_exp = str(day_dict.get("hotel_experience") or "").strip()
    score_hotel = 100.0
    if len(hotel_exp.split()) < 20:
        score_hotel -= 30
        failed_rules.append("Hotel experience description too short (<20 words)")
    if selected_hotels and not any(h in hotel_exp.lower() for h in selected_hotels):
        score_hotel -= 25
        failed_rules.append("Hotel experience does not reference any mandatory selected hotel")
    section_scores["hotel_experience"] = max(0.0, score_hotel)

    # 5. Expert Insider Notes (Weight: 15%)
    insider = str(day_dict.get("expert_insider_notes") or "").strip()
    score_insider = 100.0
    if len(insider.split()) < 15:
        score_insider -= 30
        failed_rules.append("Expert insider notes too short (<15 words)")
    if any(p in insider.lower() for p in GENERIC_PLACEHOLDERS):
        score_insider -= 30
        failed_rules.append("Insider notes contain generic tourism statement")
    section_scores["expert_insider_notes"] = max(0.0, score_insider)

    # 6. Transition to Tomorrow (Weight: 10%)
    transition = str(day_dict.get("next_day_transition") or "").strip()
    score_trans = 100.0
    if len(transition.split()) < 10:
        score_trans -= 30
        failed_rules.append("Next day transition too short (<10 words)")
    section_scores["next_day_transition"] = max(0.0, score_trans)

    # Compute Weighted Overall Score matching Architecture Diagram
    weights = {
        "destination_story": 0.20,
        "todays_journey": 0.20,
        "curated_experience": 0.20,
        "hotel_experience": 0.20,
        "expert_insider_notes": 0.15,
        "next_day_transition": 0.05,
    }

    overall_score = sum(section_scores[k] * weights[k] for k in weights)
    return (overall_score, section_scores, failed_rules)


def validate_consistency(days: list[dict[str, Any]], request: TripRequest) -> tuple[bool, list[str]]:
    """
    Stage 3: Cross-Day Consistency & Timeline Logic Validator.
    Checks sequence, inter-island transport matching, and arrival/departure rules.
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

        # Inter-island transport logic check
        if idx > 0:
            prev_island = str(days[idx - 1].get("primary_island") or "").strip().lower()
            curr_island = str(day.get("primary_island") or "").strip().lower()
            if prev_island and curr_island and prev_island != curr_island:
                combined_text = (journey + " " + str(day.get("travel_movement") or "")).lower()
                if "ferry" not in combined_text and "transfer" not in combined_text and "flight" not in combined_text:
                    errors.append(f"Day {day_num} changes island from {prev_island} to {curr_island} but journey mentions no transfer/ferry.")

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
        all_section_scores: dict[str, list[float]] = {k: [] for k in REQUIRED_NARRATIVE_FIELDS}

        for idx, day in enumerate(days):
            score, sec_scores, rules = evaluate_quality_score(day, request)
            day_scores.append(score)
            all_failed_rules.extend([f"Day {idx+1}: {r}" for r in rules])
            for k, s in sec_scores.items():
                all_section_scores[k].append(s)

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
