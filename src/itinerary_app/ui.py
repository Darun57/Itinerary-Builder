import os
from datetime import timedelta

import pandas as pd
import streamlit as st

from itinerary_app.company_knowledge import build_recommendation_bundle
from itinerary_app.config import APP_SUBTITLE, APP_TITLE, BRAND_NAME, DEFAULT_MODEL
from itinerary_app.data_loader import load_hotels
from itinerary_app.google_service import generate_itinerary_stream
from itinerary_app.models import TripRequest
from itinerary_app.pdf_service import generate_luxury_pdf


TRIP_TYPES = ["Family", "Honeymoon", "Friends", "Corporate", "Solo"]
BUDGET_CATEGORIES = ["Budget", "Premium", "Luxury"]
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
TRAVEL_STYLES = [
    "Relaxation",
    "Adventure",
    "Luxury",
    "Family Bonding",
    "Photography",
    "Culture",
    "Wellness",
    "Honeymoon",
    "Nature Exploration",
]
TRIP_PACES = ["Relaxed", "Balanced", "Fast-Paced"]
HOTEL_CATEGORIES = ["3 Star", "4 Star", "5 Star", "Ultra Luxury"]
ROOM_TYPES = ["Standard", "Deluxe", "Premium", "Suite", "Villa"]
ROOM_VIEWS = ["No Preference", "Garden View", "Pool View", "Sea View"]
HOTEL_ISLAND_OPTIONS = ["Port Blair", "Swaraj Dweep", "Shaheed Dweep", "Diglipur"]
HOTEL_CATEGORY_FILTERS = ["2 Star", "3 Star", "4 Star", "5 Star", "Ultra Luxury"]
TRANSFER_TYPES = ["Shared", "Private", "Luxury Private"]
FERRY_OPTIONS = ["Makruzz", "Nautika", "Green Ocean", "Government Ferry"]
MEAL_PLANS = ["Breakfast Only", "MAP", "AP"]
FOOD_PREFERENCES = ["Vegetarian", "Non Vegetarian", "Jain", "Vegan"]
ACTIVITY_PREFERENCES = [
    "Scuba Diving",
    "Snorkeling",
    "Sea Walk",
    "Glass Bottom Boat",
    "Parasailing",
    "Kayaking",
    "Jet Ski",
    "Sunset Cruise",
    "Candlelight Dinner",
    "Spa Experience",
    "Trekking",
    "Fishing",
    "Island Hopping",
    "Photography Tour",
]
SPECIAL_OCCASIONS = ["Honeymoon", "Anniversary", "Birthday Celebration", "Proposal", "Family Celebration"]
ACCESSIBILITY_REQUIREMENTS = ["Senior Citizen Friendly", "Wheelchair Friendly", "Infant Friendly"]
RESTRICTIONS_EXCLUSIONS = [
    "No Water Activities",
    "No Early Morning Activities",
    "No Long Road Journeys",
    "No Adventure Activities",
]
DESTINATION_OPTIONS = [
    "Port Blair",
    "Swaraj Dweep (Havelock Island)",
    "Shaheed Dweep (Neil Island)",
    "Baratang Island",
    "Ross Island (Netaji Subhash Chandra Bose Island)",
    "North Bay Island",
    "Jolly Buoy Island",
    "Red Skin Island",
    "Chidiya Tapu",
    "Wandoor Beach",
    "Cinque Island",
    "Long Island",
    "Rangat",
    "Mayabunder",
    "Diglipur",
    "Ross and Smith Islands",
    "Little Andaman",
    "Barren Island (Cruise View)",
    "Interview Island",
    "Cellular Jail",
    "Light & Sound Show",
    "Corbyn's Cove Beach",
    "Flag Point",
    "Marina Park",
    "Anthropological Museum",
    "Samudrika Marine Museum",
    "Chatham Saw Mill",
    "Fisheries Museum",
    "Jogger's Park",
    "Radhanagar Beach",
    "Elephant Beach",
    "Kala Pathar Beach",
    "Scuba Diving",
    "Snorkeling",
    "Kayaking",
    "Bharatpur Beach",
    "Laxmanpur Beach",
    "Natural Bridge",
    "Sitapur Beach",
    "Limestone Cave",
    "Mud Volcano",
    "Mangrove Boat Ride",
    "Ross & Smith Sandbar",
    "Saddle Peak Trek",
    "Kalipur Beach",
]
NATIONALITIES = [
    "Indian",
    "American",
    "British",
    "Australian",
    "Canadian",
    "German",
    "French",
    "Singaporean",
    "Japanese",
    "Chinese",
    "Malaysian",
    "Indonesian",
    "Thai",
    "Sri Lankan",
    "Nepalese",
    "Bangladeshi",
    "Pakistani",
    "UAE",
    "Emirati",
    "Saudi",
    "Qatari",
    "Kuwaiti",
    "Omani",
    "Bahraini",
    "Italian",
    "Spanish",
    "Portuguese",
    "Dutch",
    "Belgian",
    "Swiss",
    "Austrian",
    "Swedish",
    "Norwegian",
    "Danish",
    "Finnish",
    "Irish",
    "Scottish",
    "New Zealander",
    "South African",
    "Kenyan",
    "Nigerian",
    "Mexican",
    "Brazilian",
    "Argentinian",
    "Chilean",
    "Colombian",
    "Peruvian",
    "Turkish",
    "Russian",
    "Ukrainian",
    "Kazakh",
    "Philippine",
    "Vietnamese",
    "Korean",
    "Taiwanese",
    "Custom...",
]
COUNTRIES_FALLBACK = [
    "India",
    "Afghanistan",
    "Albania",
    "Algeria",
    "Argentina",
    "Australia",
    "Austria",
    "Bangladesh",
    "Belgium",
    "Bhutan",
    "Brazil",
    "Canada",
    "Chile",
    "China",
    "Colombia",
    "Denmark",
    "Egypt",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hong Kong",
    "Iceland",
    "Indonesia",
    "Ireland",
    "Israel",
    "Italy",
    "Japan",
    "Kenya",
    "Kuwait",
    "Malaysia",
    "Maldives",
    "Mexico",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nigeria",
    "Norway",
    "Oman",
    "Pakistan",
    "Philippines",
    "Qatar",
    "Russia",
    "Saudi Arabia",
    "Singapore",
    "South Africa",
    "South Korea",
    "Spain",
    "Sri Lanka",
    "Sweden",
    "Switzerland",
    "Thailand",
    "Turkey",
    "UAE",
    "United Kingdom",
    "United States",
    "Vietnam",
    "Custom...",
]
MODEL_OPTIONS = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
]


def _apply_styles() -> None:
    st.markdown(
        """
        <style>
            .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
            .app-brand { font-size: 0.95rem; letter-spacing: 0.08em; text-transform: uppercase; color: #7b8b9a; }
            .app-subtitle { color: #586574; margin-top: -0.4rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _resolve_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
    entered_key = st.sidebar.text_input(
        "Google AI Studio API key",
        value=env_key,
        type="password",
        placeholder="AIza...",
        help="Paste a free Gemini API key from Google AI Studio. This overrides GEMINI_API_KEY for this session.",
    ).strip()
    return entered_key


def _join_selected(values: object) -> str:
    if isinstance(values, list):
        return ", ".join(str(value).strip() for value in values if str(value).strip())
    return str(values).strip()


def _normalize_location(value: object) -> str:
    return str(value or "").strip().lower()


def _normalize_island_name(value: object) -> str:
    text = _normalize_location(value)
    if not text:
        return ""
    for island in HOTEL_ISLAND_OPTIONS:
        if _normalize_location(island) in text or text in _normalize_location(island):
            return island
    return ""


def _select_with_custom(label: str, options: list[str], default_value: str, custom_placeholder: str) -> str:
    selected = st.selectbox(label, options, index=options.index(default_value) if default_value in options else 0)
    if selected == "Custom...":
        return st.text_input(f"Custom {label}", placeholder=custom_placeholder).strip()
    return selected


def _default_daily_destinations(day_number: int) -> list[str]:
    templates = {
        1: ["Port Blair"],
        2: ["Ross Island (Netaji Subhash Chandra Bose Island)", "North Bay Island"],
        3: ["Swaraj Dweep (Havelock Island)"],
        4: ["Swaraj Dweep (Havelock Island)"],
        5: ["Shaheed Dweep (Neil Island)"],
        6: ["Shaheed Dweep (Neil Island)"],
        7: ["Port Blair"],
    }
    return templates.get(day_number, ["Port Blair"])


def _filtered_hotels(hotel_islands: list[str], category: str) -> list[dict[str, str]]:
    hotels = load_hotels()
    if hotels.empty:
        return []

    island_keys = [_normalize_location(island) for island in hotel_islands if _normalize_location(island)]
    location_series = hotels["location"].astype(str).str.lower()
    category_series = hotels["category"].astype(str).str.lower()
    availability_series = hotels["availability_status"].fillna("Available").astype(str).str.lower()

    filter_mask = availability_series.ne("fully booked")
    if island_keys:
        filter_mask = filter_mask & location_series.isin(island_keys)
    if category:
        filter_mask = filter_mask & category_series.eq(category.lower())
    hotels = hotels[filter_mask].copy()

    if hotels.empty:
        return []

    return [
        {
            "hotel_name": str(row["hotel_name"]).strip(),
            "location": str(row["location"]).strip(),
            "category": str(row["category"]).strip(),
            "description": str(row.get("description") or "").strip(),
        }
        for _, row in hotels.iterrows()
    ]


def _hotel_option_label(hotel: dict[str, str]) -> str:
    return f'{hotel["hotel_name"]} — {hotel["location"]} ({hotel["category"]})'


def _sync_selected_hotels(hotel_options: list[dict[str, str]]) -> list[str]:
    available_names = [hotel["hotel_name"] for hotel in hotel_options]
    selected = st.session_state.get("selected_hotels", [])
    if isinstance(selected, list):
        selected = [name for name in selected if name in available_names]
    else:
        selected = []
    if not selected and available_names and "selected_hotels" not in st.session_state:
        selected = available_names[: min(3, len(available_names))]
    st.session_state.selected_hotels = selected
    return selected


def _hotel_islands_from_destinations(destinations: list[str]) -> list[str]:
    islands: list[str] = []
    for destination in destinations:
        island = _normalize_island_name(destination)
        if island and island not in islands:
            islands.append(island)
    return islands


def _sync_daily_plan_state(number_of_days: int) -> None:
    previous_day_count = int(st.session_state.get("daily_plan_day_count", 0))
    if previous_day_count != number_of_days:
        for key in list(st.session_state.keys()):
            if key.startswith("daily_plan_day_"):
                try:
                    day_number = int(key.rsplit("_", 1)[-1])
                except ValueError:
                    continue
                if day_number > number_of_days:
                    del st.session_state[key]
        st.session_state.daily_plan_day_count = number_of_days

    for day_number in range(1, number_of_days + 1):
        key = f"daily_plan_day_{day_number}"
        if key not in st.session_state:
            st.session_state[key] = _default_daily_destinations(day_number)


def _format_daily_island_plan(number_of_days: int) -> str:
    lines: list[str] = []
    for day_number in range(1, number_of_days + 1):
        destinations = st.session_state.get(f"daily_plan_day_{day_number}", [])
        if isinstance(destinations, list) and destinations:
            lines.append(f"Day {day_number}: {', '.join(destinations)}")
        else:
            lines.append(f"Day {day_number}: Port Blair")
    return "\n".join(lines)


def _render_travel_planner() -> tuple[list[str], str, str, object, object, object, bool, int, int]:
    with st.expander("Travel Information", expanded=True):
        top_left, top_right = st.columns(2)
        with top_left:
            selected_destinations = st.multiselect(
                "Destination Selection",
                DESTINATION_OPTIONS,
                default=st.session_state.get("selected_destinations", ["Port Blair"]),
                key="selected_destinations",
            )
            number_of_days = st.number_input(
                "Number of Days",
                min_value=1,
                value=int(st.session_state.get("trip_number_of_days", 7)),
                step=1,
                key="trip_number_of_days",
            )
            arrival_date = st.date_input("Arrival Date", key="trip_arrival_date")
            travel_month = st.selectbox("Travel Month", MONTHS, index=0, key="trip_travel_month")
        with top_right:
            number_of_nights = max(int(number_of_days) - 1, 0)
            departure_date = arrival_date + timedelta(days=number_of_nights)
            st.info(
                f"**Number of Nights:** {number_of_nights}\n\n**Departure Date:** {departure_date.strftime('%d %b %Y')}"
            )
            flexible_travel_dates = st.toggle("Flexible Travel Dates", value=False, key="trip_flexible_dates")

        _sync_daily_plan_state(int(number_of_days))
        st.markdown("**Daily Island Plan**")
        for day_number in range(1, int(number_of_days) + 1):
            st.multiselect(
                f"Day {day_number} Destination(s)",
                DESTINATION_OPTIONS,
                key=f"daily_plan_day_{day_number}",
                default=st.session_state.get(f"daily_plan_day_{day_number}", _default_daily_destinations(day_number)),
            )

    selected_destination_text = ", ".join(selected_destinations).strip()
    if not selected_destination_text:
        selected_destination_text = "Andaman Islands"

    return (
        selected_destinations,
        selected_destination_text,
        _format_daily_island_plan(int(number_of_days)),
        arrival_date,
        departure_date,
        travel_month,
        flexible_travel_dates,
        int(number_of_days),
        int(number_of_nights),
    )


def _build_request(form_data: dict[str, object]) -> TripRequest:
    return TripRequest(
        customer_name=str(form_data["customer_name"]).strip(),
        lead_id=str(form_data["lead_id"]).strip(),
        customer_nationality=str(form_data["customer_nationality"]).strip(),
        customer_country=str(form_data["customer_country"]).strip(),
        customer_email=str(form_data["customer_email"]).strip(),
        customer_phone_number=str(form_data["customer_phone_number"]).strip(),
        destination=str(form_data["destination"]).strip(),
        selected_destinations=str(form_data["selected_destinations"]).strip(),
        daily_island_plan=str(form_data["daily_island_plan"]).strip(),
        number_of_nights=int(form_data["number_of_nights"]),
        number_of_days=int(form_data["number_of_days"]),
        arrival_date=str(form_data["arrival_date"]),
        departure_date=str(form_data["departure_date"]),
        travel_month=str(form_data["travel_month"]),
        flexible_travel_dates=bool(form_data["flexible_travel_dates"]),
        trip_type=str(form_data["trip_type"]),
        budget_category=str(form_data["budget_category"]),
        number_of_adults=int(form_data["number_of_adults"]),
        number_of_children=int(form_data["number_of_children"]),
        number_of_infants=int(form_data["number_of_infants"]),
        number_of_senior_citizens=int(form_data["number_of_senior_citizens"]),
        travel_style=", ".join(form_data["travel_style"]) if isinstance(form_data["travel_style"], list) else str(form_data["travel_style"]),
        trip_pace=str(form_data["trip_pace"]),
        hotel_category_preference=str(form_data["hotel_category_preference"]),
        room_type_preference=str(form_data["room_type_preference"]),
        room_view_preference=str(form_data["room_view_preference"]),
        hotel_selection_islands=_join_selected(form_data["hotel_selection_islands"]),
        selected_hotels=_join_selected(form_data["selected_hotels"]),
        transfer_type=str(form_data["transfer_type"]),
        preferred_ferries=_join_selected(form_data["preferred_ferries"]),
        meal_plan=str(form_data["meal_plan"]),
        food_preferences=_join_selected(form_data["food_preferences"]),
        preferred_activities=_join_selected(form_data["preferred_activities"]),
        special_occasions=_join_selected(form_data["special_occasions"]),
        accessibility_requirements=_join_selected(form_data["accessibility_requirements"]),
        restrictions_exclusions=_join_selected(form_data["restrictions_exclusions"]),
        internal_staff_notes=str(form_data["internal_staff_notes"]).strip(),
        special_requests=str(form_data["special_requests"]).strip(),
    )


def _render_recommendation_list(items: list[str], empty_message: str) -> None:
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.caption(empty_message)


def _render_recommendations(request: TripRequest) -> None:
    bundle = build_recommendation_bundle(request)

    with st.expander("AI Recommendations", expanded=False):
        top_left, top_right = st.columns(2)

        with top_left:
            st.markdown("**Hotels**")
            _render_recommendation_list(
                [
                    f'{row["hotel_name"]} - {row["location"]} ({row["category"]})'
                    for _, row in bundle.hotels.iterrows()
                ],
                "No hotel recommendations yet.",
            )
            st.markdown("**Activities**")
            _render_recommendation_list(
                [
                    f'{row["activity_name"]} - {row["location"]} ({row["category"]})'
                    for _, row in bundle.activities.iterrows()
                ],
                "No activity recommendations yet.",
            )

        with top_right:
            st.markdown("**Ferries**")
            _render_recommendation_list(
                [
                    f'{row["from_location"]} to {row["to_location"]} - {row["operator"]}'
                    for _, row in bundle.ferries.iterrows()
                ],
                "No ferry recommendations yet.",
            )
            st.markdown("**Destinations**")
            _render_recommendation_list(
                [f'{row["destination_name"]} - {row["best_for"]}' for _, row in bundle.destinations.iterrows()],
                "No destination recommendations yet.",
            )


def _generate_itinerary(api_key: str, model: str, request: TripRequest) -> None:
    preview = st.empty()
    with st.spinner("Generating itinerary..."):
        try:
            itinerary_parts = []
            for text_chunk in generate_itinerary_stream(api_key=api_key, model=model, request=request):
                itinerary_parts.append(text_chunk)
                preview.markdown("".join(itinerary_parts))
            itinerary = "".join(itinerary_parts).strip()
            if not itinerary:
                raise ValueError("Gemini returned an empty itinerary.")
        except ValueError as error:
            preview.empty()
            st.error(str(error))
        except Exception as error:
            preview.empty()
            st.error(f"Gemini could not generate the itinerary: {error}")
        else:
            preview.empty()
            version_number = len(st.session_state.itinerary_versions) + 1
            st.session_state.current_request = request
            st.session_state.generated_itinerary = itinerary
            st.session_state.edited_itinerary = itinerary
            st.session_state.itinerary_text = itinerary
            st.session_state.itinerary_versions.append(
                {"label": f"Version {version_number}", "request": request, "itinerary": itinerary}
            )


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":palm_tree:", layout="wide")
    _apply_styles()

    if "itinerary_text" not in st.session_state:
        st.session_state.itinerary_text = ""
    if "current_request" not in st.session_state:
        st.session_state.current_request = None
    if "generated_itinerary" not in st.session_state:
        st.session_state.generated_itinerary = ""
    if "edited_itinerary" not in st.session_state:
        st.session_state.edited_itinerary = ""
    if "itinerary_versions" not in st.session_state:
        st.session_state.itinerary_versions = []

    (
        selected_destination_choices,
        destination_text,
        daily_island_plan,
        arrival_date,
        departure_date,
        travel_month,
        flexible_travel_dates,
        number_of_days,
        number_of_nights,
    ) = _render_travel_planner()

    st.markdown(f'<div class="app-brand">{BRAND_NAME}</div>', unsafe_allow_html=True)
    st.title(APP_TITLE)
    st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

    st.sidebar.header("Generation settings")
    default_model_index = MODEL_OPTIONS.index(DEFAULT_MODEL) if DEFAULT_MODEL in MODEL_OPTIONS else 0
    model = st.sidebar.selectbox(
        "Gemini model",
        MODEL_OPTIONS,
        index=default_model_index,
        help="Flash-Lite is fastest. Use 3.5 Flash only if you need a richer draft.",
    )
    api_key = _resolve_api_key()
    if api_key:
        st.sidebar.success("API key ready. Paste a new key above if the current one expired.")

    with st.form("itinerary_form", clear_on_submit=False):
        st.subheader("Trip details")
        with st.expander("Customer Information", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                customer_name = st.text_input("Customer Name", placeholder="Enter customer name")
                lead_id = st.text_input("Lead ID", placeholder="DT-2026-001")
                customer_nationality = _select_with_custom(
                    "Customer Nationality",
                    NATIONALITIES,
                    "Indian",
                    "Enter nationality",
                )
            with top_right:
                try:
                    import pycountry

                    country_options = sorted({country.name for country in pycountry.countries})
                    if "India" not in country_options:
                        country_options.insert(0, "India")
                except Exception:
                    country_options = COUNTRIES_FALLBACK
                customer_country = _select_with_custom(
                    "Customer Country",
                    country_options,
                    "India",
                    "Enter country",
                )
                customer_email = st.text_input("Customer Email", placeholder="Enter email")
                customer_phone_number = st.text_input("Customer Phone Number", placeholder="Enter phone number")

        with st.expander("Travel Party", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                number_of_adults = st.number_input("Adults", min_value=0, value=2, step=1)
                number_of_infants = st.number_input("Infants", min_value=0, value=0, step=1)
            with top_right:
                number_of_children = st.number_input("Children", min_value=0, value=0, step=1)
                number_of_senior_citizens = st.number_input("Senior Citizens", min_value=0, value=0, step=1)

        with st.expander("Trip Style", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                trip_type = st.selectbox("Trip Type", TRIP_TYPES, index=0)
                budget_category = st.selectbox("Budget Category", BUDGET_CATEGORIES, index=2)
            with top_right:
                travel_style = st.multiselect("Travel Style", TRAVEL_STYLES, default=["Luxury"])
                trip_pace = st.selectbox("Trip Pace", TRIP_PACES, index=1)

        with st.expander("Accommodation Preferences", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                room_type_preference = st.selectbox("Room Type", ROOM_TYPES, index=1)
            with top_right:
                room_view_preference = st.selectbox("Room View Preference", ROOM_VIEWS, index=0)

        with st.expander("Hotel Selection", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                use_manual_island_entry = st.toggle("Enter hotel islands manually", value=False)
                if use_manual_island_entry:
                    hotel_selection_islands = st.multiselect(
                        "Destination Islands",
                        HOTEL_ISLAND_OPTIONS,
                        default=[island for island in HOTEL_ISLAND_OPTIONS if island in _hotel_islands_from_destinations(selected_destination_choices)] or ["Port Blair"],
                        key="manual_hotel_islands",
                        help="Choose the islands that should control the hotel inventory filter.",
                    )
                else:
                    hotel_selection_islands = _hotel_islands_from_destinations(selected_destination_choices)
                    st.info(f"Linked islands: {', '.join(hotel_selection_islands) if hotel_selection_islands else 'Port Blair'}")
            with top_right:
                hotel_category_preference = st.selectbox("Hotel Category", HOTEL_CATEGORY_FILTERS, index=2)

            available_hotels = _filtered_hotels(hotel_selection_islands, hotel_category_preference)
            selected_hotel_names = _sync_selected_hotels(available_hotels)
            hotel_name_options = [hotel["hotel_name"] for hotel in available_hotels]

            if hotel_name_options:
                st.multiselect(
                    "Available Hotels",
                    hotel_name_options,
                    key="selected_hotels",
                    default=selected_hotel_names,
                    help="Only hotels matching the selected islands, category, and availability are shown.",
                )
                st.caption("Matching hotels")
                for hotel in available_hotels[:6]:
                    st.markdown(f"- {_hotel_option_label(hotel)}")
            else:
                st.session_state.selected_hotels = []
                st.caption("No matching hotels found for the current island and category filters.")

        with st.expander("Transport Preferences", expanded=False):
            top_left, top_right = st.columns(2)
            with top_left:
                transfer_type = st.selectbox("Transfer Type", TRANSFER_TYPES, index=1)
            with top_right:
                preferred_ferries = st.multiselect("Preferred Ferry", FERRY_OPTIONS, default=[])

        with st.expander("Meal Preferences", expanded=False):
            top_left, top_right = st.columns(2)
            with top_left:
                meal_plan = st.selectbox("Meal Plan", MEAL_PLANS, index=0)
            with top_right:
                food_preferences = st.multiselect("Food Preference", FOOD_PREFERENCES, default=[])

        with st.expander("Activity Preferences", expanded=False):
            preferred_activities = st.multiselect("Activities", ACTIVITY_PREFERENCES, default=[])

        with st.expander("Special Occasions", expanded=False):
            special_occasions = st.multiselect("Special Occasions", SPECIAL_OCCASIONS, default=[])

        with st.expander("Accessibility Requirements", expanded=False):
            accessibility_requirements = st.multiselect(
                "Accessibility Requirements",
                ACCESSIBILITY_REQUIREMENTS,
                default=[],
            )

        with st.expander("Restrictions / Exclusions", expanded=False):
            restrictions_exclusions = st.multiselect(
                "Restrictions / Exclusions",
                RESTRICTIONS_EXCLUSIONS,
                default=[],
            )

        with st.expander("Special Requests", expanded=False):
            special_requests = st.text_area(
                "Special Requests",
                placeholder="Scuba diving, candlelight dinner, senior citizen friendly, adventure activities, relaxation focused...",
                height=130,
            )

        with st.expander("Internal Staff Notes", expanded=False):
            internal_staff_notes = st.text_area(
                "Internal Staff Notes",
                placeholder="VIP Guest, Repeat Customer, High Budget Client, Needs Sea View Rooms...",
                height=160,
            )

        submitted = st.form_submit_button("Generate Professional Itinerary", use_container_width=True, type="primary")

    request = _build_request(
        {
            "customer_name": customer_name,
            "lead_id": lead_id,
            "customer_nationality": customer_nationality,
            "customer_country": customer_country,
            "customer_email": customer_email,
            "customer_phone_number": customer_phone_number,
            "destination": destination_text,
            "selected_destinations": destination_text,
            "daily_island_plan": daily_island_plan,
            "number_of_nights": number_of_nights,
            "number_of_days": number_of_days,
            "arrival_date": arrival_date,
            "departure_date": departure_date,
            "travel_month": travel_month,
            "flexible_travel_dates": flexible_travel_dates,
            "trip_type": trip_type,
            "budget_category": budget_category,
            "number_of_adults": number_of_adults,
            "number_of_children": number_of_children,
            "number_of_infants": number_of_infants,
            "number_of_senior_citizens": number_of_senior_citizens,
            "travel_style": travel_style,
            "trip_pace": trip_pace,
            "hotel_category_preference": hotel_category_preference,
            "room_type_preference": room_type_preference,
            "room_view_preference": room_view_preference,
            "hotel_selection_islands": hotel_selection_islands,
            "selected_hotels": st.session_state.get("selected_hotels", []),
            "transfer_type": transfer_type,
            "preferred_ferries": preferred_ferries,
            "meal_plan": meal_plan,
            "food_preferences": food_preferences,
            "preferred_activities": preferred_activities,
            "special_occasions": special_occasions,
            "accessibility_requirements": accessibility_requirements,
            "restrictions_exclusions": restrictions_exclusions,
            "internal_staff_notes": internal_staff_notes,
            "special_requests": special_requests,
        }
    )

    if customer_name.strip() or special_requests.strip() or destination_text.strip():
        _render_recommendations(request)

    if submitted:
        if not api_key:
            st.error("Add a Google AI Studio API key in the sidebar or set GEMINI_API_KEY in your environment.")
        elif not customer_name.strip():
            st.error("Customer Name is required.")
        elif int(number_of_days) < int(number_of_nights):
            st.error("Number of Days should be equal to or greater than Number of Nights.")
        elif int(number_of_adults) + int(number_of_children) == 0:
            st.error("Add at least one traveller.")
        else:
            _generate_itinerary(api_key=api_key, model=model, request=request)

    st.subheader("Itinerary editor")
    if st.session_state.itinerary_text:
        top_left, top_right = st.columns([3, 1])
        with top_left:
            if st.session_state.itinerary_versions:
                version_labels = [version["label"] for version in st.session_state.itinerary_versions]
                st.caption(f"Saved versions: {', '.join(version_labels)}")
        with top_right:
            if st.button("Generate Another Version", use_container_width=True):
                current_request = st.session_state.current_request or request
                if not api_key:
                    st.error("Add a Google AI Studio API key in the sidebar or set GEMINI_API_KEY in your environment.")
                else:
                    _generate_itinerary(api_key=api_key, model=model, request=current_request)
        st.text_area(
            "Edit the generated itinerary below",
            key="itinerary_text",
            height=650,
        )
        st.session_state.edited_itinerary = st.session_state.itinerary_text
        st.download_button(
            "Download itinerary",
            data=st.session_state.itinerary_text,
            file_name="darun-tourism-itinerary.txt",
            mime="text/plain",
            use_container_width=True,
        )
        pdf_request = st.session_state.current_request or request
        st.download_button(
            "Generate Luxury PDF",
            data=generate_luxury_pdf(pdf_request, st.session_state.itinerary_text),
            file_name="darun-tourism-itinerary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.caption("Copy the final itinerary directly from this editor or download it as a text file.")
    else:
        st.info("Generate an itinerary to start editing it here.")
