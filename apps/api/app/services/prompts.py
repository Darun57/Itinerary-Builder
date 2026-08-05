"""
Prompt builders for Gemini AI itinerary generation.

Only ``build_prompt`` is used by the live application (called from google_service.py).
``SYSTEM_PROMPT`` is exported for reference.
"""
from app.services.company_knowledge import build_company_context_for_request
from app.schemas.trip import TripRequest


SYSTEM_PROMPT = """\
You are the Narrative Intelligence Engine powering a world-class luxury tourism SaaS.
Your responsibility is to create day-wise itinerary narratives that feel as though they were personally written by a team of experts: an experienced destination expert, historian, luxury travel consultant, hotel concierge, and logistics planner.

The final output must NEVER resemble a timetable or schedule. The traveller must feel that every single day has been intentionally and personally designed for them based on their exact profile, budget, and preferences.

Return ONLY valid JSON.

Schema:
{
  "days": [
    {
      "day_number": 1,
      "title": "string",
      "subtitle": "string",
      "primary_island": "string",
      "travel_movement": "string",
      "destination_story": "string",
      "todays_journey": "string",
      "hotel_experience": "string",
      "curated_experience": "string",
      "expert_insider_notes": "string",
      "next_day_transition": "string",
      "hotel": "string",
      "activities": ["string"],
      "attractions": ["string"],
      "image_keyword": "string"
    }
  ]
}

============================================================
NARRATIVE PERSONAS & SECTION RESPONSIBILITIES
============================================================

To achieve human-level luxury travel writing, adopt these distinct personas for each JSON field:

1. SECTION: destination_story & title/subtitle
   PERSONA: The Luxury Travel Consultant & Destination Historian
   - Set the emotional tone using evocative, premium vocabulary (e.g., pristine, bespoke, azure, sanctuary).
   - Form the core theme around the Primary Island.
   - Write a rich 40+ word narrative paragraph explaining the island's geography, history, or unique mood.
   - Inject 1-2 factual, historical, or geographical insights ONLY when relevant (e.g., Kala Pani history for Cellular Jail, or geological mud volcanoes for Baratang).

2. SECTION: todays_journey & travel_movement
   PERSONA: The Logistics Planner
   - Detail the physical journey: starting point, transfers, ferry operator, crossing duration.
   - Write a 30+ word paragraph that clearly details the transfer method and route.
   - You MUST explain WHY this specific route or transport is taken (e.g., "To maximize your time on Havelock, a morning Makruzz ferry provides a swift, scenic crossing").

3. SECTION: curated_experience
   PERSONA: The Luxury Travel Consultant
   - Write a 40+ word paragraph weaving Scheduled Attractions and Scheduled Activities naturally into the day.
   - Focus on sensory and emotional details (golden hour photography, marine biodiversity, crystal-clear turquoise waters).

4. SECTION: hotel_experience
   PERSONA: The Hotel Concierge
   - MUST use the exact Mandatory Selected Hotel specified in THAT DAY'S <MandatoryHotel> XML directive.
   - NEVER use a hotel from a different island or day. Every day's hotel_experience paragraph MUST explicitly describe the stay at that specific day's <MandatoryHotel>.
   - Write a 40+ word paragraph detailing the stay at this specific hotel.
   - You MUST explain WHY this hotel matches the traveler's Budget, Trip Type, and Accessibility Requirements.
   - Integrate the Meal Plan seamlessly (e.g., "Return for your included half-board dining experience").
   - Address any Special Requests or Internal Staff Notes subtly as Concierge Touches (e.g., noting an anniversary setup).

5. SECTION: expert_insider_notes
   PERSONA: The Local Guide
   - Write a 25+ word paragraph providing highly specific, practical advice (e.g., footwear for reefs, tidal warnings, BSNL network dependency, cash necessities, permit requirements).

6. SECTION: next_day_transition
   PERSONA: The Logistics Planner
   - Write a 20+ word closing paragraph with seamless narrative continuity connecting today's experiences to tomorrow's journey. No abrupt endings.

============================================================
STRICT ANTI-REPETITION & STYLISTIC RULES
============================================================
- ABSOLUTELY FORBIDDEN SEQUENTIAL OPENERS: "First,", "Next,", "Then,", "The morning starts", "The morning opens", "As the afternoon approaches", "Your day begins", "The afternoon continues", "The evening concludes".
- HOOK CONSTRAINTS: The first sentence of EVERY paragraph must begin with either a sensory detail, a geographical/historical fact, or an action verb. NEVER start a paragraph with a time marker.
- FORBIDDEN PHRASES: "Enjoy sightseeing...", "Relax and unwind...", "Guest comfort...", "Polished close...", "Wind down...", "Comfortable overnight stay...".
- DYNAMIC FOCUS: Vary the narrative lens. Do not echo the same structure every day.
- Every paragraph must be 100% unique and bespoke to the daily XML directives.

============================================================
STRICT DAY-MAPPING CONSTRAINTS
============================================================
- DAY 1 MUST BE ARRIVAL ONLY: Focus on airport arrival, warm island welcome, transfer to hotel, check-in, and initial evening exploration. NEVER mention departure or return flights on Day 1.
- FINAL DAY MUST BE DEPARTURE ONLY: Focus on final morning leisure, hotel check-out, souvenir shopping, private transfer to Veer Savarkar International Airport, and return flight. NEVER mention arrival on the final day.
"""


def _format_list(value: object) -> str:
    if not value:
        return "None"
    if isinstance(value, list):
        if value and hasattr(value[0], "day_number"):
            lines = []
            for dp in value:
                parts = []
                if hasattr(dp, "primary_island") and dp.primary_island:
                    parts.append(str(dp.primary_island))
                if hasattr(dp, "attractions") and dp.attractions:
                    parts.append(f"Locations: {', '.join(dp.attractions)}")
                if hasattr(dp, "activities") and dp.activities:
                    parts.append(f"Activities: {', '.join(dp.activities)}")
                if hasattr(dp, "ferry") and dp.ferry and str(dp.ferry).strip().lower() != "none":
                    timing_str = f" at {dp.ferry_timing}" if hasattr(dp, "ferry_timing") and dp.ferry_timing else ""
                    parts.append(f"Ferry: {dp.ferry}{timing_str}")
                
                content = " | ".join(parts) if parts else "No plan"
                lines.append(f"Day {dp.day_number}: {content}")
            return "\n".join(lines)
        return ", ".join(str(v) for v in value)
    return str(value)


def _resolve_primary_island(island_candidate: str, attractions: list[str], day_num: int, total_days: int) -> str:
    text = (str(island_candidate or "") + " " + " ".join(attractions or [])).lower()
    if "havelock" in text or "swaraj" in text or "radhanagar" in text or "kalapathar" in text or "elephant beach" in text:
        return "Swaraj Dweep (Havelock)"
    if "neil" in text or "shaheed" in text or "laxmanpur" in text or "bharatpur" in text or "natural bridge" in text:
        return "Shaheed Dweep (Neil)"
    if "baratang" in text or "limestone" in text or "mud volcano" in text:
        return "Baratang Island"
    if "ross" in text or "north bay" in text:
        return "Ross Island & North Bay"
    if "diglipur" in text or "saddle peak" in text or "ross & smith" in text:
        return "Diglipur"
    if "port blair" in text or "cellular jail" in text or "corbyn" in text or "marina park" in text or "chidiya tapu" in text or "wandoor" in text or "museum" in text:
        return "Port Blair"
    
    if day_num == 1 or day_num == total_days:
        return "Port Blair"
    return island_candidate if island_candidate and island_candidate.lower() not in ["andaman and nicobar islands", "andaman"] else "Port Blair"


def _format_day_by_day_database_directives(request: TripRequest) -> str:
    total_days = int(request.number_of_days or 1)
    daily_plans = request.daily_island_plan or []
    hotels = request.selected_hotels or []
    
    directives = []
    for day_num in range(1, total_days + 1):
        dp = next((p for p in daily_plans if p.day_number == day_num), None)
        
        is_first_day = (day_num == 1)
        is_last_day = (day_num == total_days)
        
        day_type = "ARRIVAL DAY" if is_first_day else ("DEPARTURE DAY" if is_last_day else "INTER-ISLAND / SIGHTSEEING DAY")
        island = _resolve_primary_island(dp.primary_island if dp else "", dp.attractions if dp else [], day_num, total_days)
        attractions = ", ".join(dp.attractions) if dp and dp.attractions else "Key island highlights"
        activities = ", ".join(dp.activities) if dp and dp.activities else "Curated luxury experiences"
        hotel = dp.hotel if dp and dp.hotel else (hotels[(day_num - 1) % len(hotels)] if hotels else "Selected Luxury Resort")
        
        transfer_info = "No inter-island ferry transfer today"
        ferry_operator = ""
        ferry_timing = ""
        transfer_type = ""
        
        if dp:
            transfer_type = dp.transfer_type or "Private Transfer"
            if dp.ferry and str(dp.ferry).strip().lower() != "none":
                ferry_operator = dp.ferry
                ferry_timing = dp.ferry_timing or "Morning"
                transfer_info = f"Ferry/Transfer: via {transfer_type} ({ferry_operator}) at {ferry_timing}"
            elif dp.transfer_type and str(dp.transfer_type).strip().lower() != "none":
                transfer_info = f"Transfer: {transfer_type}"
        
        day_role = (
            "STRICT MANDATE: Day 1 is ONLY ARRIVAL & WELCOME. Narrative MUST focus strictly on landing at Veer Savarkar International Airport, warm private driver greeting, hotel transfer, check-in, and initial evening exploration. NEVER mention departure, return flights, takeoff, luggage drop-off, souvenir shopping, or airport security on Day 1."
            if is_first_day else (
                "STRICT MANDATE: This is the FINAL DAY DEPARTURE. Narrative MUST focus on final morning leisure, hotel check-out, souvenir shopping, private transfer to Veer Savarkar International Airport, and return flight. DO NOT mention arrival or arrival flights."
                if is_last_day else
                "NARRATIVE ROLE: Focus on island exploration, ferry transfers, sightseeing, and immersive activities."
            )
        )
        
        directive = f"""
<Day day_number="{day_num}" role="{day_type}">
  <PrimaryIsland>{island}</PrimaryIsland>
  <Attractions>{attractions}</Attractions>
  <Activities>{activities}</Activities>
  <MandatoryHotel>{hotel}</MandatoryHotel>
  <Logistics>
    <TransportMode>{transfer_type}</TransportMode>
    <Operator>{ferry_operator}</Operator>
    <Timing>{ferry_timing}</Timing>
    <Description>{transfer_info}</Description>
  </Logistics>
  <ContextualDirectives>
    <DayRole>{day_role}</DayRole>
  </ContextualDirectives>
</Day>
"""
        directives.append(directive.strip())
        
    return "\n\n".join(directives)


def build_prompt(request: TripRequest) -> str:
    """
    Build the single consolidated Gemini prompt for itinerary generation.
    """
    company_context = build_company_context_for_request(request)
    day_directives = _format_day_by_day_database_directives(request)
    
    return f"""\
{SYSTEM_PROMPT}

Write a structured JSON itinerary adhering strictly to the XML database directives and constraints below.

<GlobalContext>
  <Customer>
    <Name>{request.customer_name}</Name>
    <Nationality>{request.customer_nationality}</Nationality>
    <Country>{request.customer_country}</Country>
    <Email>{request.customer_email}</Email>
    <Phone>{request.customer_phone_number}</Phone>
  </Customer>
  <TripSpecs>
    <Destination>{request.destination}</Destination>
    <SelectedDestinations>{_format_list(request.selected_destinations)}</SelectedDestinations>
    <Duration>{request.number_of_days} days / {request.number_of_nights} nights</Duration>
    <ArrivalDate>{request.arrival_date}</ArrivalDate>
    <DepartureDate>{request.departure_date}</DepartureDate>
    <TravelMonth>{request.travel_month}</TravelMonth>
    <FlexibleTravelDates>{request.flexible_travel_dates}</FlexibleTravelDates>
    <TripType>{request.trip_type}</TripType>
    <BudgetCategory>{request.budget_category}</BudgetCategory>
    <Travellers>{request.number_of_adults} adults, {request.number_of_children} children, {request.number_of_infants} infants, {request.number_of_senior_citizens} senior citizens</Travellers>
    <TravelStyle>{_format_list(request.travel_style)}</TravelStyle>
    <TripPace>{request.trip_pace}</TripPace>
    <HotelCategoryPreference>{request.hotel_category_preference}</HotelCategoryPreference>
    <RoomTypePreference>{request.room_type_preference}</RoomTypePreference>
    <RoomViewPreference>{request.room_view_preference}</RoomViewPreference>
  </TripSpecs>
  <ServiceContext>
    <SelectedHotels>{_format_list(request.selected_hotels)}</SelectedHotels>
    <PreferredActivities>{_format_list(request.preferred_activities)}</PreferredActivities>
    <TransferType>{request.transfer_type}</TransferType>
    <PreferredFerries>{_format_list(request.preferred_ferries)}</PreferredFerries>
    <MealPlan>{request.meal_plan}</MealPlan>
    <DietaryPreferences>{_format_list(request.food_preferences)}</DietaryPreferences>
    <AccessibilityRequirements>{_format_list(request.accessibility_requirements)}</AccessibilityRequirements>
    <RestrictionsExclusions>{_format_list(request.restrictions_exclusions)}</RestrictionsExclusions>
    <SpecialOccasions>{_format_list(request.special_occasions)}</SpecialOccasions>
    <SpecialRequests>{request.special_requests}</SpecialRequests>
    <InternalStaffNotes>{request.internal_staff_notes}</InternalStaffNotes>
  </ServiceContext>
</GlobalContext>

============================================================
AUTHORITATIVE DAY-BY-DAY SAAS DATABASE DIRECTIVES:
============================================================
{day_directives}

============================================================
COMPANY INVENTORY CONTEXT:
============================================================
{company_context}

Formatting requirements:
- Generate exactly {request.number_of_days} day objects in the "days" array, indexed from day_number 1 to {request.number_of_days}.
- EVERY DAY OBJECT MUST INCLUDE ALL 6 NARRATIVE SECTIONS: destination_story, todays_journey, hotel_experience, curated_experience, expert_insider_notes, next_day_transition.
- Output JSON only. Populate every field. Do not include markdown, prose, or code fences.
"""


# ---------------------------------------------------------------------------
# Back-compat alias so google_service.py can be updated in one place
# ---------------------------------------------------------------------------
build_fast_prompt_text = build_prompt
