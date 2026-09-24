"""Destination planning engine and AI prompt builder for additive regions (Rajasthan, Jammu & Kashmir).

Gathers structured destination intelligence (locations, attractions, activities, movements),
verifies feasibility, and instructs Gemini to act as a narrator and personalizer
WITHOUT inventing unverified inventory, hotels, prices, or transit feasibility.
"""
from __future__ import annotations

import json
from typing import Any, Optional
from app.schemas.trip import TripRequest
from app.services.destination_registry import (
    build_destination_context,
    get_movement,
    load_day_plans,
    load_destinations,
    normalize_region,
)


def get_default_day_plan_template(region: str, nights: int) -> Optional[dict[str, Any]]:
    """Look up a seeded day plan template matching the nights count."""
    templates = load_day_plans(region)
    for t in templates:
        if t.get("nights") == nights:
            return t
    # Fallback to closest or first template
    return templates[0] if templates else None


def build_destination_prompt(request: TripRequest) -> str:
    """
    Build a strictly structured prompt for Gemini using official destination intelligence.
    Enforces the 'AI vs Deterministic' rule: Gemini narrate and personalizes but NEVER invents.
    """
    region = request.destination
    context = build_destination_context(region)
    dest_name = context.get("config", {}).get("name", region)
    total_days = int(request.number_of_days or 1)
    daily_plans = request.daily_island_plan or []

    # Format structured locations & attractions for the prompt
    loc_summary = []
    for loc in context.get("destinations", []):
        loc_id = loc.get("id")
        loc_name = loc.get("name")
        attrs = [a.get("name") for a in context.get("attractions", []) if a.get("destination_id") == loc_id]
        acts = [a.get("name") for a in context.get("activities", []) if a.get("destination_id") == loc_id]
        loc_summary.append(
            f"- {loc_name} ({loc_id}): Attractions: {', '.join(attrs) if attrs else 'None seeded'}; "
            f"Activities: {', '.join(acts) if acts else 'None seeded'}"
        )

    # Format movements available
    mov_summary = []
    for mov in context.get("movements", []):
        from_id = mov.get("from_destination_id", "").split(":")[-1].title()
        to_id = mov.get("to_destination_id", "").split(":")[-1].title()
        min_m = mov.get("estimated_duration_minutes_min", 0)
        max_m = mov.get("estimated_duration_minutes_max", 0)
        mov_summary.append(f"- {from_id} -> {to_id} ({mov.get('mode', 'road')}): ~{min_m}-{max_m} mins (Planning estimate)")

    # Build day-by-day directives based on user request or template
    day_directives = []
    for day_num in range(1, total_days + 1):
        dp = next((p for p in daily_plans if p.day_number == day_num), None)
        is_first_day = (day_num == 1)
        is_last_day = (day_num == total_days)

        loc = dp.primary_island if dp and dp.primary_island else "Selected Destination Hub"
        attractions = ", ".join(dp.attractions) if dp and dp.attractions else "Curated regional sights"
        hotel = dp.hotel if dp and dp.hotel and dp.hotel.lower() not in ["none", ""] else "Selected Hotel / Boutique Stay"
        transfer = dp.transfer_type if dp and dp.transfer_type else "Private Air-Conditioned Chauffeur Transfer"

        # Movement tracking
        prev_loc = (
            daily_plans[day_num - 2].primary_island
            if day_num > 1 and len(daily_plans) >= day_num - 1
            else None
        )
        movement_note = ""
        if prev_loc and prev_loc != loc:
            mov = get_movement(region, prev_loc, loc)
            if mov:
                movement_note = (
                    f"INTERCITY MOVEMENT: Traveling from {prev_loc} to {loc}. "
                    f"Estimated duration: {mov.get('estimated_duration_minutes_min')}-{mov.get('estimated_duration_minutes_max')} minutes. "
                    f"Must allocate dedicated travel time in the day narrative."
                )

        day_directive = f"""
<Day day_number="{day_num}">
  <Location>{loc}</Location>
  <Attractions>{attractions}</Attractions>
  <MandatoryHotel>{hotel}</MandatoryHotel>
  <Transfer>{transfer}</Transfer>
  <Movement>{movement_note}</Movement>
  <IsDepartureDay>{'true' if is_last_day else 'false'}</IsDepartureDay>
</Day>
"""
        day_directives.append(day_directive.strip())

    directives_block = "\n\n".join(day_directives)

    prompt = f"""
You are the Narrative Intelligence Engine for Velqairn luxury travel proposals.
You are generating a bespoke, highly refined itinerary for {dest_name}.

CRITICAL SYSTEM CONSTRAINTS:
1. Return ONLY valid JSON matching the exact schema specified below.
2. DO NOT INVENT hotels, prices, or room types. Use only the provided hotel directives or refer to them as "your reserved luxury accommodation".
3. DO NOT INVENT impossible transit times. Respect the intercity road travel and mountain movement durations provided.
4. For departure day (is_departure_day = true), focus on morning check-out, private airport transfer, and sincere farewell gratitude.
5. In 'image_keyword', supply a concise, destination-specific keyword (e.g., '{region.lower()}_fort', '{region.lower()}_lake', etc.).

OFFICIAL DESTINATION INTELLIGENCE:
Locations & Sights:
{chr(10).join(loc_summary)}

Key Verified Intercity Movements:
{chr(10).join(mov_summary)}

DAY DIRECTIVES:
{directives_block}

JSON SCHEMA REQUIRED:
{{
  "days": [
    {{
      "day_number": 1,
      "title": "string",
      "subtitle": "string",
      "primary_island": "string",
      "travel_movement": "string",
      "is_departure_day": false,
      "visiting_places": "string (practical sightseeing narrative)",
      "destination_story": "string (cultural/historical beauty and significance)",
      "todays_journey": "string (transport and movement logistics)",
      "hotel_experience": "string (accommodation comfort and hospitality)",
      "hotel": "string",
      "activities": ["string"],
      "attractions": ["string"],
      "image_keyword": "string"
    }}
  ]
}}
"""
    return prompt.strip()
