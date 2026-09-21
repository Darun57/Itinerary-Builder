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
    "cellular jail": "Cellular Jail National Memorial",
    "light and sound show": "Cellular Jail Light and Sound Show",
    "ross island": "Ross Island (Netaji Subhash Chandra Bose Island)",
    "north bay": "North Bay Island & Coral Reef",
    "radhanagar beach": "Radhanagar Beach Sunset",
    "elephant beach": "Elephant Beach & Water Sports",
    "kalapathar beach": "Kalapathar Beach",
    "natural bridge": "Natural Rock Bridge",
    "laxmanpur beach": "Laxmanpur Beach Sunset",
    "bharatpur beach": "Bharatpur Beach & Water Sports",
    "chidiya tapu": "Chidiya Tapu Sunset Point",
    "corbyns cove": "Corbyn's Cove Beach",
    "corbyn's cove": "Corbyn's Cove Beach",
    "baratang": "Baratang Island & Limestone Caves",
    "limestone caves": "Baratang Limestone Caves",
    "mud volcano": "Baratang Mud Volcano",
    "jolly buoy": "Jolly Buoy Island Coral Exploration",
    "wandoor": "Wandoor Marine National Park",
    "scuba diving": "Scuba Diving Experience",
    "snorkeling": "Snorkeling Experience",
    "snorkelling": "Snorkeling Experience",
    "sea walk": "Undersea Walk Experience",
    "parasailing": "Parasailing Experience",
    "kayaking": "Mangrove Kayaking Experience",
    "sunset cruise": "Havelock / Port Blair Sunset Cruise",
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
    ("cellular jail", "Cellular Jail", "attractions"),
    ("light and sound", "Cellular Jail Light and Sound Show", "activities"),
    ("ross island", "Ross Island", "attractions"),
    ("north bay", "North Bay Island", "attractions"),
    ("radhanagar beach", "Radhanagar Beach", "attractions"),
    ("elephant beach", "Elephant Beach", "attractions"),
    ("kalapathar beach", "Kalapathar Beach", "attractions"),
    ("natural bridge", "Natural Rock Bridge", "attractions"),
    ("laxmanpur beach", "Laxmanpur Beach", "attractions"),
    ("bharatpur beach", "Bharatpur Beach", "attractions"),
    ("chidiya tapu", "Chidiya Tapu", "attractions"),
    ("corbyn's cove", "Corbyn's Cove Beach", "attractions"),
    ("corbyns cove", "Corbyn's Cove Beach", "attractions"),
    ("limestone caves", "Baratang Limestone Caves", "attractions"),
    ("mud volcano", "Baratang Mud Volcano", "attractions"),
    ("jolly buoy", "Jolly Buoy Island", "attractions"),
    ("wandoor", "Wandoor Beach", "attractions"),
    ("port blair", "Port Blair", "destinations"),
    ("swaraj dweep", "Swaraj Dweep (Havelock)", "destinations"),
    ("havelock", "Swaraj Dweep (Havelock)", "destinations"),
    ("shaheed dweep", "Shaheed Dweep (Neil)", "destinations"),
    ("neil island", "Shaheed Dweep (Neil)", "destinations"),
    ("baratang", "Baratang", "destinations"),
    ("diglipur", "Diglipur", "destinations"),
    ("rangat", "Rangat", "destinations"),
    ("mayabunder", "Mayabunder", "destinations"),
    ("long island", "Long Island", "destinations"),
    ("little andaman", "Little Andaman", "destinations"),
    ("scuba diving", "Scuba Diving", "activities"),
    ("snorkeling", "Snorkeling", "activities"),
    ("snorkelling", "Snorkeling", "activities"),
    ("sea walk", "Sea Walk", "activities"),
    ("parasailing", "Parasailing", "activities"),
    ("kayaking", "Mangrove Kayaking", "activities"),
    ("jet ski", "Jet Skiing", "activities"),
    ("glass bottom boat", "Glass Bottom Boat Ride", "activities"),
    ("candlelight dinner", "Beachside Candlelight Dinner", "activities"),
]


PRIMARY_DESTINATION_ORDER = {
    "attractions": [
        "Cellular Jail",
        "Ross Island",
        "North Bay Island",
        "Radhanagar Beach",
        "Elephant Beach",
        "Kalapathar Beach",
        "Natural Rock Bridge",
        "Laxmanpur Beach",
        "Bharatpur Beach",
        "Chidiya Tapu",
        "Corbyn's Cove Beach",
        "Baratang Limestone Caves",
        "Jolly Buoy Island",
    ],
    "destinations": [
        "Port Blair",
        "Swaraj Dweep (Havelock)",
        "Shaheed Dweep (Neil)",
        "Baratang",
        "Ross Island",
        "North Bay Island",
        "Diglipur",
        "Rangat",
        "Little Andaman",
    ],
    "activities": [
        "Cellular Jail Light and Sound Show",
        "Scuba Diving Introductory Dive",
        "Elephant Beach Snorkelling & Water Sports",
        "Radhanagar Beach Sunset Visit",
        "Baratang Mangrove Boat Ride & Caves",
        "Chidiya Tapu Sunset Safari",
        "Havelock Mangrove Kayaking",
        "North Bay Glass Bottom Boat Ride",
        "Undersea Sea Walk Experience",
        "Beachside Candlelight Dinner",
    ],
}


# ---------------------------------------------------------------------------
# Policy data constants (business data)
# ---------------------------------------------------------------------------
THINGS_TO_DO_CATEGORIES = [
    ("HERITAGE & CULTURE", [
        ("Cellular Jail Sound & Light Show", "₹350 per person", "Historic light and sound performance narrating the Indian freedom struggle at Cellular Jail.", False),
        ("Ross Island Heritage Walk", "₹800 per person", "Guided exploration of British colonial ruins, church, bakery, and free-roaming deer.", False),
        ("Anthropological Museum Visit", "₹250 per person", "Insight into the indigenous tribal communities and cultural history of the Andaman and Nicobar Islands.", False),
        ("Samudrika Marine Museum", "₹200 per person", "Curated naval museum showcasing Andaman marine life, shells, corals, and tribal heritage.", False),
    ]),
    ("WATER & BOAT EXPERIENCES", [
        ("Elephant Beach Water Sports", "₹2,500 per person", "Speedboat transfer with complimentary snorkeling and optional jet ski or banana ride.", False),
        ("Havelock Scuba Diving Experience", "₹4,500 per person", "PADI-guided discovery scuba dive with underwater photography and coral exploration.", False),
        ("North Bay Coral Reef Snorkeling", "₹1,800 per person", "Guided reef snorkeling session around North Bay's pristine coral gardens.", False),
        ("Sea Walk at Elephant Beach", "₹3,800 per person", "Helmet diving walking on the seabed surrounded by colorful tropical fish.", False),
        ("Glass Bottom Boat Ride", "₹1,200 per person", "Undersea coral and marine life viewing through a specialized transparent boat hull.", False),
    ]),
    ("PREMIUM EXPERIENCES", [
        ("Beachside Candlelight Dinner", "₹6,500 per couple", "Intimate private table on the beach under the stars with customized multi-course dining.", True),
        ("Private Speedboat Charter", "On request", "Exclusive speed boat hire for bespoke island transfers and secluded beach excursions.", True),
        ("Sunset Cruise & High Tea", "₹2,500 per person", "Scenic evening coastal cruise along the shores of Port Blair with refreshments.", False),
    ]),
    ("ADVENTURE & NATURE", [
        ("Baratang Limestone Caves Trip", "₹3,000 per person", "Full-day excursion through tribal reserve forest and mangrove creeks to limestone caves.", False),
        ("Chidiya Tapu Sunset Safari", "₹1,600 per person", "Scenic coastal drive to Chidiya Tapu for dramatic sunset views over the Bay of Bengal.", False),
        ("Havelock Mangrove Kayaking", "₹2,500 per person", "Guided night or dawn kayaking through calm mangrove channels and bioluminescent waters.", False),
        ("Mount Harriet / Hope Town Trek", "₹1,500 per person", "Nature trail through tropical rainforest with panoramic views of the Andaman archipelago.", False),
    ]),
    ("FOOD & WELLNESS", [
        ("Andaman Seafood Cooking Class", "₹2,400 per person", "Hands-on introduction to Andaman fresh seafood preparation and local island spices.", False),
        ("Port Blair Local Market Food Walk", "₹1,200 per person", "Guided evening food walk through Aberdeen Bazaar sampling local island snacks and delicacies.", False),
        ("Ayurvedic Island Spa & Wellness", "₹2,800 per person", "Rejuvenating wellness and massage session inspired by tropical coastal botanicals.", False),
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
    "All airport, hotel, sightseeing, and activity transfers by private air-conditioned vehicle as per the itinerary.",
    "River, boat, or ferry tickets expressly specified in the confirmed travel plan.",
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
