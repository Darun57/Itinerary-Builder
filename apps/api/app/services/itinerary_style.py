"""
Day-Wise Itinerary Style System & Narrative Formatters.

Provides a modular strategy pattern for formatting daily itinerary content:
1. LuxuryNarrativeFormatter (Default): Rich storytelling, destination context, luxury paragraphs.
2. SimpleItineraryFormatter: Short, operational, bullet-based travel-agency schedule inspired by Andaman on-ground operations.

Both formatters consume the exact same Single Source of Truth (SSOT) from TripRequest and DayPlan.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import re

from app.schemas.trip import TripRequest, DayPlan
from app.services.destination_registry import (
    is_andaman_destination,
    get_destination_display_name,
    get_destination_base_location,
)


def _clean_str(val: Any) -> str:
    return str(val or "").strip()


class BaseDayWiseFormatter(ABC):
    """Abstract strategy for formatting day-wise itinerary content."""

    @abstractmethod
    def format_day(
        self,
        day_idx: int,
        day_dict: Dict[str, Any],
        dp: Optional[DayPlan],
        request: TripRequest,
        total_days: int,
        is_departure: bool,
        last_night_hotel: str,
    ) -> Dict[str, Any]:
        """Format a single day dictionary according to the style rules."""
        pass

    @abstractmethod
    def get_style_name(self) -> str:
        """Return the unique identifier of the style."""
        pass


class LuxuryNarrativeFormatter(BaseDayWiseFormatter):
    """
    STYLE 1 — LUXURY NARRATIVE
    Preserves the existing Velqairn day-wise output:
    - Visiting Places And Destination Story (2 distinct paragraphs)
    - Today's Journey (opens with 'For the places highlighted above...')
    - Hotel Experience
    - Departure & Farewell Narrative on final day
    """

    def get_style_name(self) -> str:
        return "luxury_narrative"

    def format_day(
        self,
        day_idx: int,
        day_dict: Dict[str, Any],
        dp: Optional[DayPlan],
        request: TripRequest,
        total_days: int,
        is_departure: bool,
        last_night_hotel: str,
    ) -> Dict[str, Any]:
        day_dict["day_wise_style"] = "luxury_narrative"

        dest = (getattr(request, "destination", "") or "").strip()
        is_andaman = is_andaman_destination(dest)
        dest_name = get_destination_display_name(dest) if not is_andaman else "Andaman Islands"
        base_loc = get_destination_base_location(dest) if not is_andaman else "Andaman Islands"

        if is_departure:
            day_dict["is_departure_day"] = True
            day_dict["title"] = "Departure"
            day_dict["subtitle"] = "Departure"
            day_dict["visiting_places"] = ""
            day_dict["destination_story"] = ""
            day_dict["todays_journey"] = ""
            day_dict["hotel_experience"] = ""
            day_dict["hotel"] = ""
            day_dict["activities"] = ["Private Airport Transfer"]
            day_dict["attractions"] = ["Departure"]

            checkout_hotel = last_night_hotel or "your resort"
            customer_name = request.customer_name or "our valued guests"

            dep_narrative = _clean_str(day_dict.get("departure_narrative"))
            if len(dep_narrative) < 30:
                if is_andaman:
                    dep_narrative = (
                        f"Enjoy a peaceful morning check-out at {checkout_hotel} with full luggage assistance. "
                        f"Your private chauffeur will pick you up for a smooth transfer to "
                        f"Port Blair airport for your flight home."
                    )
                else:
                    dep_narrative = (
                        f"Enjoy a peaceful morning check-out at {checkout_hotel} with full luggage assistance. "
                        f"Your private chauffeur will pick you up for a smooth departure transfer to the "
                        f"airport for your flight home."
                    )
            day_dict["departure_narrative"] = dep_narrative

            farewell_narrative = _clean_str(day_dict.get("farewell_narrative"))
            if len(farewell_narrative) < 30:
                if is_andaman:
                    farewell_narrative = (
                        f"Darun Tourism extends its heartfelt gratitude to {customer_name} and family "
                        f"for choosing us. It was our genuine pleasure crafting your Andaman Islands trip memories, "
                        f"and we look forward to welcoming you back in the future."
                    )
                else:
                    farewell_narrative = (
                        f"Darun Tourism extends its heartfelt gratitude to {customer_name} and family "
                        f"for choosing us. It was our genuine pleasure crafting your {dest_name} trip memories, "
                        f"and we look forward to welcoming you back in the future."
                    )
            day_dict["farewell_narrative"] = farewell_narrative
            return day_dict

        # Normal Day
        day_dict["is_departure_day"] = False
        day_dict["departure_narrative"] = ""
        day_dict["farewell_narrative"] = ""

        # Title / Subtitle
        island = dp.primary_island if dp else day_dict.get("primary_island") or base_loc
        if not day_dict.get("title") or day_dict.get("title") == "Departure":
            day_dict["title"] = f"Exploring {island}"
        if not day_dict.get("subtitle"):
            day_dict["subtitle"] = "Coastal Highlights & Heritage Discovery" if is_andaman else f"Highlights & Heritage of {island}"

        # Today's Journey
        journey = _clean_str(day_dict.get("todays_journey"))
        if not journey.startswith("For the places highlighted above, "):
            if journey:
                day_dict["todays_journey"] = f"For the places highlighted above, {journey[0].lower() + journey[1:] if len(journey) > 1 else journey}"
            else:
                region_label = "the Andaman Islands" if is_andaman else dest_name
                day_dict["todays_journey"] = (
                    "For the places highlighted above, private chauffeur transfers ensure "
                    f"comfortable transportation and effortless sightseeing across {region_label} throughout the day."
                )

        # Hotel Experience
        assigned_hotel = dp.hotel if dp and dp.hotel else (
            request.selected_hotels[day_idx % len(request.selected_hotels)]
            if request.selected_hotels else ""
        )
        if assigned_hotel:
            day_dict["hotel"] = assigned_hotel
            current_hotel_exp = _clean_str(day_dict.get("hotel_experience"))
            if len(current_hotel_exp) < 20 or assigned_hotel.lower() not in current_hotel_exp.lower():
                day_dict["hotel_experience"] = (
                    f"A peaceful stay at {assigned_hotel}, offering comfortable accommodation, "
                    f"relaxing oceanfront surroundings, and warm hospitality—perfect for unwinding "
                    f"after your journey."
                )

        # Visiting Places & Destination Story
        if not day_dict.get("visiting_places"):
            attractions = ", ".join(dp.attractions) if dp and dp.attractions else ("scenic coastal landmarks" if is_andaman else "scenic regional landmarks")
            day_dict["visiting_places"] = (
                f"Begin the day with curated visits to {attractions}. "
                f"Enjoy serene beachside walks, immersive sightseeing, and memorable coastal discovery."
                if is_andaman else
                f"Begin the day with curated visits to {attractions}. "
                f"Enjoy immersive sightseeing, regional culture, and memorable exploration."
            )
        if not day_dict.get("destination_story"):
            island_label = dp.primary_island if dp else base_loc
            if is_andaman:
                day_dict["destination_story"] = (
                    f"{island_label} showcases the stunning beauty of the Andaman Islands, famous for their "
                    f"golden shorelines, tropical greenery, and rich coastal culture."
                )
            else:
                day_dict["destination_story"] = (
                    f"{island_label} showcases the authentic charm and distinctive character of {dest_name}, "
                    f"celebrated for rich heritage, scenic landscapes, and vibrant local experiences."
                )

        return day_dict


class SimpleItineraryFormatter(BaseDayWiseFormatter):
    """
    STYLE 2 — SIMPLE ITINERARY
    Operational, clear, short, bullet-based travel agency itinerary format.
    Focuses on:
    • Where they are going
    • What they are doing
    • How they are moving
    • Where they are staying
    • What happens next
    """

    def get_style_name(self) -> str:
        return "simple_itinerary"

    def _generate_short_title(
        self,
        day_idx: int,
        island: str,
        attractions: List[str],
        is_departure: bool,
        destination: str = "",
    ) -> str:
        if is_departure:
            return "Departure"

        attractions_clean = [a for a in attractions if a.lower() != "departure"]
        is_andaman = is_andaman_destination(destination)

        if day_idx == 0:
            if is_andaman:
                if any("corbyn" in a.lower() or "cellular" in a.lower() for a in attractions_clean):
                    return "Arrival & Port Blair Sightseeing"
                return "Arrival at Port Blair"

            # Destination-aware generic arrival title
            dest_name = get_destination_display_name(destination)
            if island and island.lower() != dest_name.lower():
                return f"Arrival & {island} Sightseeing"
            return f"Arrival in {dest_name}"

        if is_andaman:
            if "havelock" in island.lower() or "swaraj" in island.lower():
                if any("radhanagar" in a.lower() for a in attractions_clean) and any("elephant" in a.lower() for a in attractions_clean):
                    return "Havelock Island Beaches"
                if any("radhanagar" in a.lower() for a in attractions_clean):
                    return "Radhanagar Beach & Sunset"
                if any("elephant" in a.lower() for a in attractions_clean):
                    return "Elephant Beach Coral Tour"
                return "Havelock Island Exploration"

            if "neil" in island.lower() or "shaheed" in island.lower():
                if any("natural bridge" in a.lower() for a in attractions_clean):
                    return "Neil Island & Natural Rock Arch"
                return "Neil Island Beach Tour"

            if "baratang" in island.lower():
                return "Baratang Limestone Cave Excursion"

            if "diglipur" in island.lower():
                return "Diglipur & Ross-Smith Twin Islands"

            if any("ross" in a.lower() for a in attractions_clean) and any("north bay" in a.lower() for a in attractions_clean):
                return "Ross & North Bay Island Tour"

        if attractions_clean:
            top_spot = attractions_clean[0]
            return f"{island} – {top_spot}"

        return f"{island} Tour"

    def format_day(
        self,
        day_idx: int,
        day_dict: Dict[str, Any],
        dp: Optional[DayPlan],
        request: TripRequest,
        total_days: int,
        is_departure: bool,
        last_night_hotel: str,
    ) -> Dict[str, Any]:
        day_dict["day_wise_style"] = "simple_itinerary"

        dest = (getattr(request, "destination", "") or "").strip()
        is_andaman = is_andaman_destination(dest)
        dest_name = get_destination_display_name(dest)
        base_loc = get_destination_base_location(dest) if not is_andaman else "Port Blair"

        island = dp.primary_island if dp else _clean_str(day_dict.get("primary_island")) or base_loc
        attractions = dp.attractions if dp and dp.attractions else (day_dict.get("attractions") or [])
        
        # SSOT: Only include activities if explicitly chosen for this specific day
        if dp is not None and getattr(dp, "activities", None) is not None:
            activities = [
                str(a).strip() for a in dp.activities
                if str(a).strip() and str(a).strip().lower() not in ("none", "no activity", "leisure", "relax", "free day")
            ]
        else:
            activities = [
                str(a).strip() for a in (day_dict.get("activities") or [])
                if str(a).strip() and str(a).strip().lower() not in ("none", "no activity", "leisure", "relax", "free day")
            ]

        assigned_hotel = dp.hotel if dp and dp.hotel else (
            request.selected_hotels[day_idx % len(request.selected_hotels)]
            if request.selected_hotels else last_night_hotel
        )
        prev_dp = request.daily_island_plan[day_idx - 1] if (request.daily_island_plan and day_idx > 0 and day_idx - 1 < len(request.daily_island_plan)) else None
        prev_hotel = prev_dp.hotel if prev_dp else ""
        hotel_changed = bool(assigned_hotel and assigned_hotel != prev_hotel)

        transfer_type = (dp.transfer_type if dp else request.transfer_type) or "Private AC Cab"
        ferry_name = (dp.ferry if dp else "") or ""
        ferry_timing = (dp.ferry_timing if dp else "") or ""

        bullets: List[str] = []

        if is_departure:
            day_dict["is_departure_day"] = True
            day_dict["title"] = "Departure"
            if is_andaman:
                day_dict["subtitle"] = "Flight Departure from Port Blair"
            else:
                day_dict["subtitle"] = f"Departure from {dest_name}"
            day_dict["hotel"] = ""

            bullets.append("Breakfast at hotel")
            if last_night_hotel:
                bullets.append(f"Check-out from {last_night_hotel} with luggage assistance")
            else:
                bullets.append("Hotel check-out and luggage assistance")

            if is_andaman:
                bullets.append("Private transfer to Veer Savarkar International Airport, Port Blair")
                bullets.append("Board scheduled return flight with memorable experiences of Andaman Darun Tours and Travels")
            else:
                bullets.append("Departure transfer to airport")
                bullets.append("Board scheduled return flight with memorable travel experiences")

            day_dict["operational_bullets"] = bullets
            day_dict["summary_intro"] = "Morning check-out followed by assisted airport transfer for your return flight home."
            if is_andaman:
                day_dict["todays_journey"] = "Private transfer from hotel to Port Blair airport."
                day_dict["farewell_narrative"] = "Thank you for traveling with Andaman Darun Tours and Travels."
            else:
                day_dict["todays_journey"] = "Departure transfer from hotel to airport."
                day_dict["farewell_narrative"] = "Thank you for traveling with Darun Tourism."
            day_dict["hotel_experience"] = "Departure day — no overnight stay."
            day_dict["visiting_places"] = ""
            day_dict["destination_story"] = ""
            day_dict["departure_narrative"] = "\n".join([f"• {b}" for b in bullets])
            return day_dict

        # Normal Day
        day_dict["is_departure_day"] = False
        day_dict["departure_narrative"] = ""
        day_dict["farewell_narrative"] = ""

        # Short day title
        short_title = self._generate_short_title(day_idx, island, attractions, is_departure=False, destination=dest)
        day_dict["title"] = short_title
        day_dict["subtitle"] = f"{island} Daily Schedule"

        # 1. Morning / Pickup / Movement
        if day_idx == 0:
            if is_andaman:
                bullets.append("Pickup from Port Blair Airport and private transfer to hotel")
            else:
                bullets.append("Arrival transfer to hotel")
            if assigned_hotel:
                bullets.append(f"Check-in at {assigned_hotel}")
            else:
                bullets.append("Check-in at hotel and settle in")
        else:
            # Check if there is ferry or inter-island transit
            if ferry_name and ferry_name.lower() != "none":
                time_str = f" ({ferry_timing})" if ferry_timing else ""
                bullets.append(f"After breakfast, transfer to jetty")
                bullets.append(f"Ferry transfer to {island} via {ferry_name}{time_str}")
                if hotel_changed:
                    bullets.append(f"Transfer to {assigned_hotel} and check-in")
            elif hotel_changed:
                bullets.append("After breakfast, check-out and transfer to hotel")
                bullets.append(f"Check-in at {assigned_hotel}")
            else:
                bullets.append("Breakfast at hotel")

        # 2. Sightseeing & Destinations
        clean_spots = [a for a in attractions if a.lower() not in ("departure", "airport transfer")]
        if clean_spots:
            bullets.append("Proceed for sightseeing:")
            for spot in clean_spots:
                bullets.append(f"  → {spot}")

        # 3. Dedicated Activities (ONLY if activities were explicitly scheduled for this day)
        clean_acts = [
            act for act in activities
            if act not in clean_spots and act.lower() not in ("sightseeing", "none", "no activity", "leisure", "relax", "free day", "")
        ]
        for act in clean_acts:
            bullets.append(f"Activity: {act}")
        day_dict["activities"] = clean_acts

        # 4. Return Transfer
        bullets.append("Return transfer to hotel")

        # 5. Overnight Stay
        if assigned_hotel:
            bullets.append(f"Overnight stay at {island} ({assigned_hotel})")
        else:
            bullets.append(f"Overnight stay at {island}")

        day_dict["operational_bullets"] = bullets

        # 1-sentence operational summary
        if day_idx == 0:
            if is_andaman:
                summary = f"Arrival at Port Blair, hotel check-in, and local sightseeing including {', '.join(clean_spots[:2]) if clean_spots else 'local landmarks'}."
            else:
                summary = f"Arrival in {dest_name}, hotel check-in, and local sightseeing including {', '.join(clean_spots[:2]) if clean_spots else 'local landmarks'}."
        elif ferry_name and ferry_name.lower() != "none":
            summary = f"Travel by ferry to {island}, check in to resort, and explore {', '.join(clean_spots[:2]) if clean_spots else 'island sights'}."
        else:
            summary = f"Explore {island} with curated visits to {', '.join(clean_spots[:2]) if clean_spots else 'scenic attractions'}."
        day_dict["summary_intro"] = summary

        # Also populate standard fields cleanly so any renderer works
        day_dict["visiting_places"] = "\n".join([f"• {b}" if not b.startswith("  →") else b for b in bullets])
        day_dict["destination_story"] = ""  # No essay in simple style
        if ferry_name and ferry_name.lower() != "none":
            day_dict["todays_journey"] = f"{transfer_type} and {ferry_name} ferry ({ferry_timing or 'scheduled departure'})."
        else:
            day_dict["todays_journey"] = f"{transfer_type} for all scheduled airport and sightseeing transfers."
        
        meal_plan = request.meal_plan or "CP (Breakfast)"
        day_dict["hotel_experience"] = f"{assigned_hotel} · Meal Plan: {meal_plan} · Overnight stay at {island}."
        day_dict["hotel"] = assigned_hotel

        return day_dict


class DayWiseNarrativeFormatter:
    """Central factory and dispatcher for day-wise itinerary formatting."""

    _formatters = {
        "luxury_narrative": LuxuryNarrativeFormatter(),
        "simple_itinerary": SimpleItineraryFormatter(),
    }

    @classmethod
    def get_formatter(cls, style_name: Optional[str]) -> BaseDayWiseFormatter:
        key = (style_name or "").strip().lower()
        return cls._formatters.get(key, cls._formatters["luxury_narrative"])

    @classmethod
    def format_day(
        cls,
        day_idx: int,
        day_dict: Dict[str, Any],
        dp: Optional[DayPlan],
        request: TripRequest,
        total_days: int,
        is_departure: bool,
        last_night_hotel: str,
    ) -> Dict[str, Any]:
        style = getattr(request, "day_wise_style", "luxury_narrative") or "luxury_narrative"
        formatter = cls.get_formatter(style)
        return formatter.format_day(
            day_idx=day_idx,
            day_dict=day_dict,
            dp=dp,
            request=request,
            total_days=total_days,
            is_departure=is_departure,
            last_night_hotel=last_night_hotel,
        )
