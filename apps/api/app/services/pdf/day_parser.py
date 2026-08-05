"""
Day itinerary parsing, context extraction, and subtitle generation.
"""
from pathlib import Path
import logging
import json
import re

LOGGER = logging.getLogger(__name__)

from app.schemas.trip import TripRequest
from app.services.pdf.constants import (
    DAY_CONTEXT_KEYWORDS,
    PRIMARY_DESTINATION_ORDER,
    SECTION_LABELS,
)
from app.services.pdf.text_utils import unique_values, clean_destination_label


import json
import re

def _clean_json_payload(raw_text: str) -> str:
    cleaned = (raw_text or "").strip()
    match = re.search(r"\{.*\}\s*$", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    return cleaned


def _clean_route_string(route: str, fallback_island: str) -> str:
    """Removes transportation details, actions, and redundant prefixes from a route string."""
    if not route:
        return fallback_island or ""
        
    route = re.sub(r'\s*(?:->|to|-)\s*', ' → ', route, flags=re.IGNORECASE).strip()
    parts = route.split(' → ')
    
    cleaned_parts = []
    for part in parts:
        lower_part = part.lower()
        # Skip parts that describe transportation or activities
        if any(word in lower_part for word in [
            "transfer", "ferry", "boat", "cruise", "excursion", "flight", 
            "check-in", "check in", "catamaran", "pickup", "drop"
        ]):
            continue
            
        # Strip common narrative prefixes
        part = re.sub(r'^(?:Arrival in|Arrival at|Departure from|Travel to|Journey to|Return to|Day trip to)\s+', '', part, flags=re.IGNORECASE).strip()
        
        if part and (not cleaned_parts or cleaned_parts[-1] != part):
            cleaned_parts.append(part)
            
    result = ' → '.join(cleaned_parts)
    return result if result else (fallback_island or "")


def split_itinerary_into_days(itinerary_text: str) -> list[dict[str, object]]:
    json_candidate = _clean_json_payload(itinerary_text)
    
    data = None
    try:
        data = json.loads(json_candidate, strict=False)
    except Exception:
        try:
            fixed_json = re.sub(r'(?<=: ")[\s\S]*?(?=",\n|"\n|\"\s*\})', lambda m: m.group(0).replace('\n', ' '), json_candidate)
            data = json.loads(fixed_json, strict=False)
        except Exception as err:
            LOGGER.warning("Could not parse itinerary JSON: %s", err)

    if isinstance(data, dict) and "days" in data and isinstance(data["days"], list):
        sections = []
        sorted_days = sorted(data["days"], key=lambda d: int(d.get("day_number") or 0))
        for day in sorted_days:
            day_num = int(day.get("day_number") or 1)
            island = day.get("primary_island") or ""
            raw_title = day.get("title") or ""
            raw_route = str(day.get("travel_movement") or island).strip()
            
            route = _clean_route_string(raw_route, island)
            if route:
                title = f"DAY {day_num} | {route}"
            else:
                title = f"DAY {day_num}"

            items = []
            if day.get("destination_story"):
                items.append({"label": "Destination Story", "content": str(day["destination_story"]).strip()})
            if day.get("todays_journey"):
                items.append({"label": "Today's Journey", "content": str(day["todays_journey"]).strip()})
            if day.get("hotel_experience"):
                items.append({"label": "Hotel Experience", "content": str(day["hotel_experience"]).strip()})
            if day.get("curated_experience"):
                items.append({"label": "Curated Experience", "content": str(day["curated_experience"]).strip()})
            
            sections.append({"heading": title, "items": items})
        if sections:
            return sections

    # Fallback: Parse markdown headings if JSON structure is absent
    markdown_sections = []
    current_heading = ""
    current_content = []
    
    for line in itinerary_text.splitlines():
        line_str = line.strip()
        if re.match(r"^#{1,3}\s*Day\s*\d+", line_str, re.IGNORECASE) or re.match(r"^Day\s*\d+[:\s]", line_str, re.IGNORECASE):
            if current_heading:
                markdown_sections.append({
                    "heading": current_heading,
                    "items": [{"label": "Itinerary Details", "content": "\n".join(current_content).strip()}]
                })
            current_heading = re.sub(r"^#{1,3}\s*", "", line_str)
            current_content = []
        elif current_heading:
            if line_str:
                current_content.append(line_str)
                
    if current_heading:
        markdown_sections.append({
            "heading": current_heading,
            "items": [{"label": "Itinerary Details", "content": "\n".join(current_content).strip()}]
        })
        
    return markdown_sections


def _extract_day_context_values(text: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {"destinations": [], "activities": [], "attractions": []}
    normalized = text.lower()
    for keyword, label, group in DAY_CONTEXT_KEYWORDS:
        if keyword in normalized and label not in values[group]:
            values[group].append(label)
    return values


def _day_plan_line(request: TripRequest, day_number: int) -> str:
    if isinstance(request.daily_island_plan, list):
        for dp in request.daily_island_plan:
            if dp.day_number == day_number:
                return f"{dp.primary_island} {' '.join(dp.attractions)}"
    return ""


def _day_text_haystack(day_section: dict[str, object], request: TripRequest, day_number: int) -> str:
    return " ".join([
        str(day_section.get("heading") or ""),
        " ".join(str(item.get("label") or "") for item in day_section.get("items", [])),
        " ".join(str(item.get("content") or "") for item in day_section.get("items", [])),
        _day_plan_line(request, day_number),
    ]).lower()


def build_day_context(
    day_section: dict[str, object],
    request: TripRequest,
    day_number: int,
    used_images: set[Path] | None = None,
) -> dict[str, object]:
    context_values = _extract_day_context_values(_day_text_haystack(day_section, request, day_number))
    primary_attractions = [v for v in PRIMARY_DESTINATION_ORDER["attractions"] if v in context_values["attractions"]]
    primary_islands = [v for v in PRIMARY_DESTINATION_ORDER["destinations"] if v in context_values["destinations"]]
    primary_activities = [v for v in PRIMARY_DESTINATION_ORDER["activities"] if v in context_values["activities"]]
    primary_beaches = [v for v in primary_attractions if "Beach" in v]
    return {
        "day_number": day_number,
        "title": str(day_section.get("heading") or f"Day {day_number}"),
        "destinations": context_values["destinations"],
        "activities": context_values["activities"],
        "attractions": context_values["attractions"],
        "primary_attractions": primary_attractions,
        "primary_beaches": primary_beaches,
        "primary_islands": primary_islands,
        "primary_activities": primary_activities,
        "used_images": used_images if used_images is not None else set(),
    }


def _join_subtitle_values(values: list[str]) -> str:
    selected = unique_values(values)[:2]
    if not selected:
        return "the Andaman Islands"
    return " & ".join(selected)


def generate_day_subtitle(day_context: dict[str, object]) -> str:
    attractions = unique_values(
        list(day_context.get("primary_attractions") or []) + list(day_context.get("attractions") or [])
    )
    beaches = unique_values(list(day_context.get("primary_beaches") or []))
    islands = unique_values(
        list(day_context.get("primary_islands") or []) + list(day_context.get("destinations") or [])
    )
    activities = unique_values(
        list(day_context.get("primary_activities") or []) + list(day_context.get("activities") or [])
    )
    title = str(day_context.get("title") or "")

    if "Departure" in title:
        return "Farewell to the Andaman Islands"
    if attractions:
        selected = attractions[:2]
        if {"Ross Island", "North Bay Island"}.issubset(set(selected)):
            return "Historic Ross & North Bay Excursion"
        beach_set = {"Radhanagar Beach", "Elephant Beach", "Kala Pathar Beach", "Bharatpur Beach", "Laxmanpur Beach", "Corbyn's Cove Beach", "Chidiya Tapu"}
        if len(selected) == 1 and selected[0] in beach_set:
            return f"Sunset at {selected[0]}"
        if len(selected) == 2:
            return f"{selected[0]} & {selected[1]} Experience"
        return f"Journey to {selected[0]}"
    if beaches:
        return f"Sunset at {beaches[0]}"
    if activities:
        return f"{_join_subtitle_values(activities[:2])} Experience"
    if islands:
        return f"Journey to {_join_subtitle_values(islands[:2])}"
    return "Journey through the Andaman Islands"
