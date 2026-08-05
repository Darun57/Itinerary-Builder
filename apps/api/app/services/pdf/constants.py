"""
All PDF rendering constants: colours, margins, fonts, keyword maps.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COLORS = {
    "navy": colors.HexColor("#0f1c2e"),
    "gold": colors.HexColor("#c8a96a"),
    "white": colors.HexColor("#ffffff"),
    "soft_white": colors.HexColor("#f8fafc"),
    "soft_grey": colors.HexColor("#64748b"),
    "line": colors.HexColor("#d6c29b"),
    "body": colors.HexColor("#334155"),
    "dark": colors.HexColor("#10202d"),
    "card": colors.HexColor("#fbfaf7"),
}

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
MARGINS = {"left": 52, "right": 52, "top": 40, "bottom": 42}
SPACING = {
    "xs": 0.05 * inch,
    "sm": 0.1 * inch,
    "md": 0.18 * inch,
    "lg": 0.28 * inch,
    "xl": 0.45 * inch,
}
PAGE_WIDTH, PAGE_HEIGHT = A4
PAGE_INNER_WIDTH = PAGE_WIDTH - MARGINS["left"] - MARGINS["right"]

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
from pathlib import Path

FONT_DIRS = [
    Path(__file__).resolve().parents[3] / "assets" / "fonts",
    Path(__file__).resolve().parents[3] / "fonts",
]
FONT_CANDIDATES = {
    "heading": ["PlayfairDisplay-Bold.ttf", "CormorantGaramond-Bold.ttf", "Times-Bold"],
    "subheading": ["PlayfairDisplay-SemiBold.ttf", "CormorantGaramond-SemiBold.ttf", "Helvetica-Bold"],
    "body": ["CormorantGaramond-Regular.ttf", "SourceSans3-Regular.ttf", "Helvetica"],
    "body_bold": ["CormorantGaramond-SemiBold.ttf", "SourceSans3-SemiBold.ttf", "Helvetica-Bold"],
}

# ---------------------------------------------------------------------------
# Text / keyword maps
# ---------------------------------------------------------------------------
SECTION_LABELS = {"morning", "afternoon", "evening", "overnight stay"}

ITINERARY_KEYWORDS = {
    "cellular jail light and sound show": "Cellular Jail Light & Sound Show",
    "radhanagar beach sunset": "Radhanagar Beach Sunset",
    "scuba diving": "Scuba Diving Experience",
    "natural bridge": "Natural Bridge Visit",
    "glass bottom boat": "Glass Bottom Boat Ride",
    "north bay": "North Bay and Ross Island",
    "ross island": "North Bay and Ross Island",
}

GENERIC_PHRASE_BLACKLIST = (
    "curated island experiences",
    "destination mood",
    "selected travel party",
    "staff-editable",
    "smooth coordination",
    "refined sense of place",
    "balanced pace",
    "elegant close to the day",
)

DAY_CONTEXT_KEYWORDS = [
    ("corbyn's cove", "Corbyn's Cove Beach", "attractions"),
    ("corbyn cove", "Corbyn's Cove Beach", "attractions"),
    ("cellular jail", "Cellular Jail", "attractions"),
    ("light and sound show", "Cellular Jail Light & Sound Show", "attractions"),
    ("radhanagar beach", "Radhanagar Beach", "attractions"),
    ("kala pathar beach", "Kala Pathar Beach", "attractions"),
    ("kala pathar", "Kala Pathar Beach", "attractions"),
    ("elephant beach", "Elephant Beach", "attractions"),
    ("natural rock bridge", "Natural Bridge", "attractions"),
    ("natural bridge", "Natural Bridge", "attractions"),
    ("bharatpur beach", "Bharatpur Beach", "attractions"),
    ("laxmanpur beach", "Laxmanpur Beach", "attractions"),
    ("chidiya tapu", "Chidiya Tapu", "attractions"),
    ("ross island", "Ross Island", "destinations"),
    ("north bay", "North Bay Island", "destinations"),
    ("swaraj dweep", "Swaraj Dweep", "destinations"),
    ("havelock island", "Swaraj Dweep", "destinations"),
    ("havelock", "Swaraj Dweep", "destinations"),
    ("shaheed dweep", "Shaheed Dweep", "destinations"),
    ("neil island", "Shaheed Dweep", "destinations"),
    ("neil", "Shaheed Dweep", "destinations"),
    ("port blair", "Port Blair", "destinations"),
    ("diglipur", "Diglipur", "destinations"),
    ("baratang", "Baratang", "destinations"),
    ("rangat", "Rangat", "destinations"),
    ("mayabunder", "Mayabunder", "destinations"),
    ("little andaman", "Little Andaman", "destinations"),
    ("scuba diving", "Scuba Diving", "activities"),
    ("snorkeling", "Snorkeling", "activities"),
    ("snorkelling", "Snorkeling", "activities"),
    ("sea walk", "Sea Walk", "activities"),
    ("glass bottom boat", "Glass Bottom Boat", "activities"),
    ("parasailing", "Parasailing", "activities"),
    ("kayaking", "Kayaking", "activities"),
    ("sunset cruise", "Sunset Cruise", "activities"),
    ("candlelight dinner", "Candlelight Dinner", "activities"),
]

PRIMARY_DESTINATION_ORDER = {
    "attractions": [
        "Cellular Jail Light & Sound Show",
        "Cellular Jail",
        "Ross Island",
        "North Bay Island",
        "Radhanagar Beach",
        "Elephant Beach",
        "Natural Bridge",
        "Bharatpur Beach",
        "Laxmanpur Beach",
        "Corbyn's Cove Beach",
        "Chidiya Tapu",
        "Kala Pathar Beach",
    ],
    "destinations": [
        "Port Blair",
        "Swaraj Dweep",
        "Shaheed Dweep",
        "Baratang",
        "Diglipur",
        "Rangat",
        "Mayabunder",
        "Little Andaman",
    ],
    "activities": [
        "Scuba Diving",
        "Snorkeling",
        "Sea Walk",
        "Glass Bottom Boat",
        "Kayaking",
        "Sunset Cruise",
        "Candlelight Dinner",
        "Parasailing",
    ],
}

# ---------------------------------------------------------------------------
# Policy data constants (business data — unchanged from original)
# ---------------------------------------------------------------------------
THINGS_TO_DO_CATEGORIES = [
    ("SCUBA EXPERIENCES", [
        ("Shore Scuba Diving", "₹3,500 per person", "Underwater discovery guided by certified diving professionals.", False),
        ("Boat Scuba Diving", "₹5,500 per person", "Coral reef exploration at selected dive sites.", False),
        ("Shore Snorkelling", "₹3,000 per person", "Guided surface-level coral viewing from the shore.", False),
        ("Boat Snorkelling", "₹5,000 per person", "Offshore marine discovery in pristine island waters.", False),
        ("Sea Walk Experience", "₹3,800 per person", "A comfortable seabed walk with close marine encounters.", False),
    ]),
    ("WATER SPORTS", [
        ("Flyboard Adventure", "₹4,500 per person", "High-powered water-jet adventure above the sea.", True),
        ("Underwater Scooter Ride", "₹6,500 per person", "Effortless underwater exploration without prior swimming experience.", True),
        ("Sea Kart Adventure", "₹3,500 per person", "Self-drive watercraft experience across turquoise waters.", False),
        ("Jet Ski Ride", "₹1,000 per person", "A short, exhilarating ride across crystal-clear sea.", False),
        ("Parasailing", "₹3,500 per person", "Aerial island and coastline views from above.", False),
        ("Banana Boat Ride", "₹800 per person", "A lively group water activity for families and friends.", False),
        ("Sofa Ride", "₹1,000 per person", "A thrilling inflatable water ride for groups.", False),
        ("Speed Boat Ride", "₹1,000 per person", "High-speed sea movement with scenic coastal views.", False),
    ]),
    ("PREMIUM EXPERIENCES", [
        ("Glass Bottom Boat Ride", "₹1,200 per person", "Coral and marine viewing without entering the water.", False),
        ("Semi-Submarine Experience", "₹1,850 per person", "Panoramic underwater viewing in air-conditioned comfort.", False),
        ("Sunset Cruise Experience", "₹5,000 per person", "A refined cruise experience during the golden evening hour.", False),
        ("Private Yacht Charter", "₹35,000 per charter", "Private luxury cruising with personalised service.", False),
    ]),
    ("ADVENTURE ACTIVITIES", [
        ("Day Kayaking", "₹3,500 per person", "Scenic paddling through calm island waters.", False),
        ("Night Mangrove Kayaking", "₹3,500 per person", "A rare night experience through mangrove channels.", False),
        ("Sport Fishing Excursion", "₹8,000 per person", "Deep-sea angling with experienced local crews.", False),
        ("Saddle Peak Trek", "₹2,500 per person", "A trek to the highest point in the Andaman Islands.", False),
    ]),
    ("ROMANTIC EXPERIENCES", [
        ("Beachside Candlelight Dinner", "₹7,500 per couple", "An intimate beach setting for special celebrations.", False),
        ("Photography Tour", "₹3,500 per person", "A curated visual journey through scenic island locations.", False),
    ]),
    ("NATURE EXPERIENCES", [
        ("Dolphin Watching Tour", "₹4,000 per person", "A chance to observe dolphins in their natural habitat.", False),
        ("Bird Watching Excursion", "₹2,500 per person", "Guided discovery of the islands' diverse avian life.", False),
        ("Limestone Cave Excursion", "₹1,500 per person", "Limestone formations reached through dense mangrove scenery.", False),
        ("Mud Volcano Excursion", "₹1,500 per person", "A rare geological attraction within the islands.", False),
        ("Bioluminescence Experience", "₹4,500 per person", "A night excursion to witness glowing marine organisms.", False),
    ]),
]

PAYMENT_POLICY_CARDS = [
    ("Booking Confirmation", "Written confirmation and the required advance payment are required to process reservations."),
    ("Advance Payment", "Hotels, ferries, cruises, and travel services are secured only after timely advance payment."),
    ("Tentative Reservations", "All bookings remain tentative until payment is received and acknowledged by the company."),
    ("Availability Clause", "Rooms, ferry seats, cruises, and services remain subject to availability at confirmation."),
    ("Balance Payment", "The remaining balance must be settled before tour commencement as per the agreed schedule."),
    ("Short Notice Bookings", "Bookings made within 30 days of arrival may require 100% payment at confirmation."),
    ("Peak Season Policy", "Festive periods, Christmas, and New Year may attract special terms and supplements."),
    ("Rate Validity", "Package rates may change without notice until the booking is formally confirmed."),
    ("Final Documentation", "Travel documents, ferry tickets, vouchers, and confirmations are issued after full payment."),
    ("Mode of Payment", "Payments may be made by bank transfer, UPI, or other approved payment methods."),
    ("Additional Charges", "Tax, entrance fee, fuel, or supplier increases after confirmation are payable by the guest."),
    ("Refund Processing", "Eligible refunds are processed after supplier refunds are received and policy terms are applied."),
]

CANCELLATION_TIMELINE = [
    ("30+ Days Before Arrival", "10% Charges", "Administrative and processing fees apply."),
    ("20-29 Days Before Arrival", "50% Charges", "Mid-window cancellation charges apply."),
    ("Less Than 20 Days", "100% Charges", "Full package cancellation charges apply."),
    ("No Show", "100% Charges", "No refund is applicable without prior notification."),
]

CANCELLATION_DETAIL_CARDS = [
    ("Peak Season Bookings", "Christmas, New Year, long weekends, and festive periods may carry separate cancellation conditions."),
    ("Flight and Ferry Cancellations", "Flights, ferries, cruises, and third-party services follow the respective supplier policies."),
    ("Unused Services", "Unused accommodation, meals, sightseeing, transfers, activities, or services are non-refundable."),
    ("Force Majeure", "No refund applies for events beyond company control, including weather, restrictions, or disruptions."),
    ("Refund Processing", "Eligible refunds may take 15 to 30 working days after supplier approval and receipt."),
    ("Amendment Charges", "Confirmed booking amendments remain subject to availability and applicable supplementary charges."),
]

TERMS_CONDITION_CARDS = [
    ("Booking Confirmation", "All bookings are subject to availability and confirmed only after advance payment and written company confirmation."),
    ("Hotel Availability", "If a confirmed hotel becomes unavailable due to operational reasons, maintenance, or overbooking, a similar category hotel shall be provided."),
    ("Check-In and Check-Out", "Hotel check-in and check-out timings are governed by individual hotel policies and may vary by property."),
    ("Transportation Services", "Vehicle services operate strictly as per the approved itinerary. Additional usage attracts supplementary charges."),
    ("Ferry Operations", "Ferry schedules remain subject to weather, operations, technical reasons, and authority directives."),
    ("Sightseeing Operations", "Sightseeing tours and activities are subject to weather, permissions, operational feasibility, and local regulations."),
    ("Weather Conditions", "Activities and locations may be modified, rescheduled, or cancelled in the interest of guest safety."),
    ("Guest Responsibility", "Guests are responsible for their personal belongings during the tour."),
    ("Travel Documents", "Guests must carry valid government-issued photo identification and any required travel documents."),
    ("Foreign Nationals", "Foreign nationals must carry valid passports, visas, and applicable Government of India or local permits."),
    ("Force Majeure", "The company is not responsible for delays, cancellations, losses, injuries, or events beyond reasonable control."),
    ("Itinerary Amendments", "The company may amend, reroute, modify, or reschedule itinerary components due to operational requirements."),
    ("Liability Limitation", "The company acts as an intermediary and is not liable for deficiencies by hotels, transport operators, activity providers, or third-party suppliers."),
    ("No Refund Policy", "No refund applies for missed sightseeing, unused services, early departures, or services not availed by the guest."),
    ("Acceptance Clause", "By confirming the booking, guests accept all terms, conditions, payment policies, and cancellation policies stated herein."),
]

INCLUSION_ITEMS = [
    "Accommodation in selected category hotels or resorts as confirmed in the final itinerary.",
    "Daily breakfast wherever included by the respective hotel or resort.",
    "All airport, hotel, sightseeing, and jetty transfers by private air-conditioned vehicle as per the itinerary.",
    "Premium inter-island ferry tickets as specified in the confirmed travel plan.",
    "All sightseeing experiences and excursions expressly mentioned in the final itinerary.",
    "Entry permits, parking charges, and applicable government taxes related to included services.",
    "Dedicated local assistance throughout the tour for a smooth on-ground experience.",
    "Similar category hotels may be provided in case of operational constraints or supplier availability changes.",
    "Vehicle assistance during medical emergencies, subject to local conditions and accessibility.",
    "Applicable taxes as per current government regulations.",
]

EXCLUSION_ITEMS = [
    "Personal expenses of any nature.",
    "Laundry, room service, telephone calls, and minibar charges.",
    "Tips, porterage, camera fees, and other discretionary guest expenses.",
    "Optional tours, activities, or experiences not expressly mentioned in the itinerary.",
    "Vehicle services during leisure periods or outside the confirmed sightseeing schedule.",
    "Additional expenses arising from delays, cancellations, weather disruptions, or force majeure events.",
    "Travel insurance, unless specifically mentioned as included.",
    "Peak season supplements, festive surcharges, and special event premiums unless included in writing.",
    "Celebration arrangements, decor, cakes, bouquets, or private dining experiences unless explicitly mentioned.",
    "Any item or service not expressly specified under the Inclusions section.",
]
