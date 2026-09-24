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
    "basilica of bom jesus": "Basilica of Bom Jesus",
    "fontainhas": "Fontainhas Heritage Quarter",
    "panaji waterfront": "Panaji Waterfront",
    "dona paula": "Dona Paula Viewpoint",
    "fort aguada": "Fort Aguada",
    "aguada": "Fort Aguada",
    "palolem beach sunset": "Palolem Beach Sunset",
    "sunset cruise": "Mandovi Sunset Cruise",
    "scuba diving": "Scuba Diving Experience",
    "snorkeling": "Snorkeling Experience",
    "snorkelling": "Snorkeling Experience",
    "grand island": "Grand Island Boat Excursion",
    "dudhsagar": "Dudhsagar Falls Excursion",
    "spice plantation": "Goan Spice Plantation Experience",
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
    ("basilica of bom jesus", "Basilica of Bom Jesus", "attractions"),
    ("se cathedral", "Se Cathedral", "attractions"),
    ("fontainhas", "Fontainhas", "attractions"),
    ("dona paula", "Dona Paula", "attractions"),
    ("miramar", "Miramar Beach", "attractions"),
    ("fort aguada", "Fort Aguada", "attractions"),
    ("aguada", "Fort Aguada", "attractions"),
    ("grand island", "Grand Island", "attractions"),
    ("palolem", "Palolem Beach", "attractions"),
    ("agonda", "Agonda Beach", "attractions"),
    ("patnem", "Patnem Beach", "attractions"),
    ("baga", "Baga", "destinations"),
    ("candolim", "Candolim", "destinations"),
    ("calangute", "Calangute", "destinations"),
    ("anjuna", "Anjuna", "destinations"),
    ("vagator", "Vagator", "destinations"),
    ("morjim", "Morjim", "destinations"),
    ("mandrem", "Mandrem", "destinations"),
    ("old goa", "Old Goa", "destinations"),
    ("dudhsagar", "Dudhsagar", "destinations"),
    ("collem", "Collem", "destinations"),
    ("panaji", "Panaji", "destinations"),
    ("divar island", "Divar Island", "destinations"),
    ("netravali", "Netravali", "destinations"),
    ("cabo de rama", "Cabo de Rama", "destinations"),
    ("scuba diving", "Scuba Diving", "activities"),
    ("snorkeling", "Snorkeling", "activities"),
    ("snorkelling", "Snorkeling", "activities"),
    ("parasailing", "Parasailing", "activities"),
    ("kayaking", "Kayaking", "activities"),
    ("sunset cruise", "Sunset Cruise", "activities"),
    ("candlelight dinner", "Candlelight Dinner", "activities"),
    ("spice plantation", "Spice Plantation", "activities"),
]


PRIMARY_DESTINATION_ORDER = {
    "attractions": [
        "Basilica of Bom Jesus",
        "Se Cathedral",
        "Fontainhas",
        "Fort Aguada",
        "Dona Paula",
        "Miramar Beach",
        "Grand Island",
        "Palolem Beach",
        "Agonda Beach",
        "Patnem Beach",
        "Cabo de Rama",
        "Dudhsagar Falls",
    ],
    "destinations": [
        "Panaji",
        "North Goa",
        "Old Goa",
        "South Goa",
        "Dudhsagar",
        "Grand Island",
    ],
    "activities": [
        "Fontainhas Heritage Walk",
        "Old Goa Heritage Circuit",
        "Mandovi Sunset River Cruise",
        "Fort Aguada Exploration",
        "Chapora Fort Sunset",
        "Baga Water Sports Session",
        "Grand Island Scuba Experience",
        "Grand Island Snorkelling",
        "Dudhsagar Jeep Excursion",
        "Goa Spice Plantation Visit",
        "Palolem Kayaking",
        "Palolem Boat & Island Cruise",
        "Goan Cooking Experience",
        "Wellness & Yoga Session",
    ],
}


# ---------------------------------------------------------------------------
# Policy data constants (business data — unchanged from original)
# ---------------------------------------------------------------------------
THINGS_TO_DO_CATEGORIES = [
    ("HERITAGE & CULTURE", [
        ("Fontainhas Heritage Walk", "₹900 per person", "Guided exploration of Panaji's Latin Quarter, architecture, lanes, and local stories.", False),
        ("Old Goa Heritage Circuit", "₹1,200 per person", "Curated visit to the Basilica of Bom Jesus, Se Cathedral, and surrounding heritage monuments.", False),
        ("Fort Aguada Exploration", "₹300 per person", "Coastal fort visit with panoramic sea views and photography time.", False),
        ("Chapora Fort Sunset", "₹250 per person", "Clifftop heritage visit timed for late-afternoon coastal light.", False),
        ("Ponda Temple Circuit", "₹1,200 per person", "Curated visit to selected temples and heritage locations in Goa's hinterland.", False),
    ]),
    ("WATER & BOAT EXPERIENCES", [
        ("Baga Water Sports Session", "₹2,500 per person", "Operator-led coastal water activities subject to sea conditions and local operating rules.", False),
        ("Grand Island Scuba Experience", "₹5,500 per person", "Boat-based diving experience subject to certification and sea conditions.", False),
        ("Grand Island Snorkelling", "₹2,200 per person", "Boat-based snorkelling around coastal reefs, subject to visibility and sea conditions.", False),
        ("Palolem Kayaking", "₹1,800 per person", "Guided kayaking session in calm coastal waters, weather and tide permitting.", False),
        ("Palolem Boat & Island Cruise", "₹1,800 per person", "Coastal boat experience to scenic points and seasonal dolphin-viewing areas.", False),
    ]),
    ("PREMIUM EXPERIENCES", [
        ("Mandovi Sunset River Cruise", "₹1,200 per person", "An evening cruise on the Mandovi River with sunset and waterfront views.", False),
        ("Private Yacht Charter", "On request", "Private luxury cruising with personalised service and a flexible route.", True),
        ("Cavelossim River & Beach Cruise", "₹2,200 per person", "Scenic Sal River and coastal outing operated according to tide and weather.", False),
    ]),
    ("ADVENTURE & NATURE", [
        ("Dudhsagar Jeep Excursion", "₹3,000 per person", "Full-day waterfall excursion combining regulated transfers with nature time.", False),
        ("Netravali Nature Trail", "₹1,800 per person", "Guided forest and village experience with seasonal nature stops.", False),
        ("Goa Spice Plantation Visit", "₹1,600 per person", "Guided plantation walk with traditional Goan lunch and farm-based storytelling.", False),
        ("South Goa Cycling Experience", "₹1,600 per person", "Guided cycling route through villages, fields, and coastal roads, weather permitting.", False),
    ]),
    ("FOOD & WELLNESS", [
        ("Goan Cooking Experience", "₹2,400 per person", "Hands-on introduction to selected Goan dishes and culinary traditions.", False),
        ("Assagao Boutique & Food Trail", "₹1,500 per person", "Leisure route through village architecture, cafes, design spaces, and local cuisine.", False),
        ("Wellness & Yoga Session", "₹1,500 per person", "Private or small-group yoga and relaxation session at a wellness-focused venue.", False),
        ("Beachside Candlelight Dinner", "On request", "An intimate beach setting for special celebrations, subject to venue availability.", True),
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
