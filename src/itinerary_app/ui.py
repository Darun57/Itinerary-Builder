import os

import streamlit as st

from itinerary_app.company_knowledge import build_recommendation_bundle
from itinerary_app.config import APP_SUBTITLE, APP_TITLE, BRAND_NAME, DEFAULT_MODEL
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


def _build_request(form_data: dict[str, object]) -> TripRequest:
    return TripRequest(
        customer_name=str(form_data["customer_name"]).strip(),
        lead_id=str(form_data["lead_id"]).strip(),
        customer_nationality=str(form_data["customer_nationality"]).strip(),
        customer_country=str(form_data["customer_country"]).strip(),
        customer_email=str(form_data["customer_email"]).strip(),
        customer_phone_number=str(form_data["customer_phone_number"]).strip(),
        destination=str(form_data["destination"]).strip(),
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
                lead_id = st.text_input("Lead ID", placeholder="Enter lead ID")
                customer_nationality = st.text_input("Customer Nationality", placeholder="Enter nationality")
            with top_right:
                customer_country = st.text_input("Customer Country", placeholder="Enter country")
                customer_email = st.text_input("Customer Email", placeholder="Enter email")
                customer_phone_number = st.text_input("Customer Phone Number", placeholder="Enter phone number")

        with st.expander("Travel Information", expanded=True):
            top_left, top_right = st.columns(2)
            with top_left:
                destination = st.text_input("Destination", value="Andaman Islands")
                number_of_days = st.number_input("Number of Days", min_value=1, value=7, step=1)
                arrival_date = st.date_input("Arrival Date")
                travel_month = st.selectbox("Travel Month", MONTHS, index=0)
            with top_right:
                number_of_nights = st.number_input("Number of Nights", min_value=1, value=6, step=1)
                departure_date = st.date_input("Departure Date")
                flexible_travel_dates = st.toggle("Flexible Travel Dates", value=False)

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
                hotel_category_preference = st.selectbox("Hotel Category", HOTEL_CATEGORIES, index=2)
                room_type_preference = st.selectbox("Room Type", ROOM_TYPES, index=1)
            with top_right:
                room_view_preference = st.selectbox("Room View Preference", ROOM_VIEWS, index=0)

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
            "destination": destination,
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

    if customer_name.strip() or special_requests.strip() or destination.strip():
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
