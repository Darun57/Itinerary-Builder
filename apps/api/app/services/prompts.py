"""
Prompt builders for Gemini AI itinerary generation.

Only ``build_prompt`` is used by the live application (called from google_service.py).
``SYSTEM_PROMPT`` is exported for reference.
"""
from app.services.company_knowledge import build_company_context_for_request
from app.schemas.trip import TripRequest


SYSTEM_PROMPT = """\
You are the Narrative Intelligence Engine powering a world-class luxury tourism SaaS.
Your responsibility is to create day-wise itinerary narratives matching a refined luxury travel proposal structure.

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
      "is_departure_day": false,
      "visiting_places": "string",
      "destination_story": "string",
      "todays_journey": "string",
      "hotel_experience": "string",
      "curated_experience": "string",
      "departure_narrative": "string",
      "farewell_narrative": "string",
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
NARRATIVE STRUCTURE & SECTION RESPONSIBILITIES
============================================================

For NORMAL ITINERARY DAYS (is_departure_day = false):
- "travel_movement": Set strictly to the canonical movement:
  * Day 1: "Port Blair" (or arrival island)
  * Inter-island transfer: "Origin to Destination" (e.g. "Port Blair to Swaraj Dweep", "Swaraj Dweep to Shaheed Dweep", "Shaheed Dweep to Port Blair")
  * Day-trip excursion returning to base hotel: "Origin to Destination Return" (e.g. "Port Blair to Baratang Island Return")
  * Exploration on same island: "Island Name" (e.g. "Swaraj Dweep")

The body will be rendered under three clean sections:
1. "Visiting Places And Destination Story" (contains TWO distinct paragraphs):
   - PARAGRAPH 1 (visiting_places): What the traveler actually visits and does during that specific day. Chronological, practical, itinerary-oriented narrative focused on actual sightseeing/activities (2–4 sentences, ~40-60 words).
   - PARAGRAPH 2 (destination_story): Character, geography, history, atmosphere, or natural beauty of the destination. Elegant premium luxury narrative explaining why the destination is special without simply repeating the sightseeing paragraph (2–4 sentences, ~40-60 words).
   (Note: Do NOT generate a separate "Curated Experience" heading; any scheduled activity details are naturally integrated into visiting_places).

2. "Today's Journey" (todays_journey):
   - Transportation & journey logistics for the day (starting point, transport mode, vehicle/ferry/boat, departure/arrival).
   - MUST ALWAYS open with the exact wording:
     "For the places highlighted above, private chauffeur transfers ensure..." or "For the places highlighted above, transfer begins early..."
   - Approximately 2–4 sentences (~35-55 words).
   - Only use real transportation/ferry/vehicle details provided in the daily directives.

3. "Hotel Experience" (hotel_experience):
   - Describes the actual hotel selected for that day from <MandatoryHotel>.
   - Atmosphere, comfort, hospitality, and relaxing surroundings.
   - Approximately 2–4 sentences (~30-55 words).
   - Example style: "A peaceful stay at [Hotel], offering comfortable accommodation, relaxing oceanfront surroundings, and warm hospitality—perfect for unwinding after your journey."

For DEPARTURE DAY (is_departure_day = true, typically the final day when it is departure-only):
- "title": "Departure"
- "subtitle": "Departure"
- "travel_movement": "Departure"
- "is_departure_day": true
- Leave visiting_places, destination_story, todays_journey, and hotel_experience as empty strings "".
The body will be rendered under:
1. "END OF THE JOURNEY" (contains TWO distinct paragraphs):
   - PARAGRAPH 1 (departure_narrative): Concludes the journey with comfortable hotel check-out, luggage assistance, and private transfer from the hotel to Veer Savarkar International Airport, ensuring a smooth and hassle-free journey home (2–3 sentences, ~35-50 words).
     Example: "Enjoy a peaceful morning check-out at [Hotel] with full luggage assistance. Your private chauffeur will pick you up for a smooth transfer to Veer Savarkar International Airport for your flight home."
   - PARAGRAPH 2 (farewell_narrative): Sincere gratitude from Darun Tourism for choosing us, pleasure in crafting memories, safe flight wishes, and welcoming them back in the future (2–4 sentences, ~40-60 words).
     Example: "Darun Tourism extends its heartfelt gratitude to [Customer Name] and family for choosing us. It was our genuine pleasure crafting your Andaman trip memories, and we look forward to welcoming you back in the future."

============================================================
STYLING & QUALITY RULES
============================================================
- Write in polished, premium travel proposal prose (as in a bespoke luxury itinerary).
- Every paragraph must be concise enough to fit the single-page layout without overflowing.
- Do NOT invent amenities, flight times, or vehicles not present in the directives.
- Keep the two paragraphs under "Visiting Places And Destination Story" distinct: Paragraph 1 is visiting/activities, Paragraph 2 is destination essence/history/beauty.
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
        is_departure_marked = is_last_day and (
            (dp and (dp.primary_island or "").strip().lower() == "departure")
            or (dp and any(str(a).strip().lower() == "departure" for a in (dp.attractions or [])))
            or is_last_day
        )
        if is_departure_marked:
            hotel = "None (Departure Day - No overnight stay)"
        else:
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
            "STRICT MANDATE: Day 1 is ONLY ARRIVAL & WELCOME (is_departure_day = false). Narrative MUST focus strictly on landing at Veer Savarkar International Airport, warm private driver greeting, hotel transfer, check-in, and initial evening exploration. Generate visiting_places, destination_story, todays_journey, and hotel_experience. NEVER mention departure, return flights, or airport security on Day 1."
            if is_first_day else (
                "STRICT MANDATE: This is the FINAL DAY DEPARTURE (is_departure_day = true). Under 'END OF THE JOURNEY', generate: (1) departure_narrative: comfortable morning at hotel, luggage assistance, private transfer from hotel to Veer Savarkar International Airport, smooth flight departure. (2) farewell_narrative: sincere thanks from Darun Tourism for choosing us, cherished memories, safe travels, and warm wishes to welcome them back. Set is_departure_day to true, title and subtitle to 'Departure'. Set visiting_places, destination_story, todays_journey, and hotel_experience to empty strings."
                if is_last_day else
                "NARRATIVE ROLE: Normal sightseeing day (is_departure_day = false). Under 'Visiting Places And Destination Story', generate: visiting_places (places and activities narrative, 2-4 sentences) and destination_story (destination history/geography/beauty, 2-4 sentences). Under 'Today's Journey', generate todays_journey (transport logistics starting with 'For the places highlighted above...', 2-4 sentences). Under 'Hotel Experience', generate hotel_experience (hotel atmosphere and hospitality, 2-4 sentences)."
            )
        )
        is_dep_str = "true" if is_last_day else "false"
        
        directive = f"""
<Day day_number="{day_num}" role="{day_type}">
  <IsDepartureDay>{is_dep_str}</IsDepartureDay>
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
- For normal itinerary days (is_departure_day = false): provide visiting_places, destination_story, todays_journey, and hotel_experience.
- For pure departure days (is_departure_day = true): provide departure_narrative and farewell_narrative.
- Output JSON only. Populate every field. Do not include markdown, prose, or code fences.
"""


# ---------------------------------------------------------------------------
# Back-compat alias so google_service.py can be updated in one place
# ---------------------------------------------------------------------------
build_fast_prompt_text = build_prompt
