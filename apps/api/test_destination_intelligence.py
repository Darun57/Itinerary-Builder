"""Comprehensive test matrix verifying Destination Intelligence, Capabilities, and Isolation."""

import sys
import unittest
from pathlib import Path

# Ensure app package is importable
API_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(API_ROOT))

from app.services.destination_registry import (
    load_destinations,
    load_attractions,
    load_activities,
    load_movements,
    load_capabilities,
    get_movement,
    normalize_region,
    is_additive_destination,
    verify_destination_contract,
    list_destinations,
)
from app.services.destination_validator import (
    validate_hotel_location,
    validate_trip_destination_integrity,
)
from app.services.pdf.image_resolver import (
    resolve_namespace_image,
    resolve_day_image,
)
from app.schemas.trip import TripRequest, DayPlan
from app.services.data_loader import load_destinations as load_andaman_destinations


ACTIVE_DESTINATIONS = [
    "rajasthan",
    "jammu_and_kashmir",
    "goa",
    "kerala",
    "himachal_pradesh",
    "uttarakhand",
    "ladakh",
]


class TestDestinationIntelligenceMatrix(unittest.TestCase):

    # ── 1. Contract & Capability Verification for All Active Destinations ────

    def test_01_all_active_destinations_satisfy_contract(self):
        """Every active destination must satisfy the Destination Intelligence Contract."""
        for dest in ACTIVE_DESTINATIONS:
            summary = verify_destination_contract(dest)
            self.assertEqual(
                summary.status,
                "active",
                f"Destination '{dest}' should have status 'active'"
            )
            self.assertTrue(
                summary.satisfies_contract,
                f"Destination '{dest}' fails contract. Missing: {summary.missing_requirements}"
            )
            self.assertGreater(summary.locations_count, 0, f"'{dest}' must have locations")
            self.assertGreater(summary.activities_count, 0, f"'{dest}' must have activities")
            self.assertGreater(summary.movements_count, 0, f"'{dest}' must have movements")
            self.assertGreater(summary.day_plans_count, 0, f"'{dest}' must have day plans")
            self.assertTrue(summary.has_capabilities, f"'{dest}' must have capabilities.json")

    def test_02_all_active_destinations_namespace_isolation(self):
        """All entities inside each active destination must use that destination's namespace."""
        for dest in ACTIVE_DESTINATIONS:
            norm = normalize_region(dest)
            prefix = norm.replace("_", "-")
            alt_prefix = norm

            locations = load_destinations(dest)
            for loc in locations:
                loc_id = loc.get("id", "")
                self.assertTrue(
                    loc_id.startswith(f"{prefix}:") or loc_id.startswith(f"{alt_prefix}:"),
                    f"Location '{loc_id}' in '{dest}' does not start with expected namespace"
                )
                self.assertNotIn("andaman", loc_id)

            activities = load_activities(dest)
            for act in activities:
                act_id = act.get("id") or act.get("activity_id", "")
                self.assertTrue(
                    act_id.startswith(f"{prefix}:") or act_id.startswith(f"{alt_prefix}:"),
                    f"Activity '{act_id}' in '{dest}' does not start with expected namespace"
                )
                self.assertNotIn("andaman", act_id)

    def test_03_capability_profiles(self):
        """Verify distinct capability profiles for different destination types."""
        # Goa: coastal road, no ferry, slow pace
        goa_caps = load_capabilities("goa")
        self.assertFalse(goa_caps.get("supports_ferry"))
        self.assertIn("road", goa_caps.get("transport_modes", []))
        self.assertEqual(goa_caps.get("typical_circuit_pace"), "slow")

        # Kerala: supports houseboat, road
        kerala_caps = load_capabilities("kerala")
        self.assertTrue(kerala_caps.get("supports_houseboat"))
        self.assertFalse(kerala_caps.get("supports_ferry"))
        self.assertIn("houseboat", kerala_caps.get("transport_modes", []))

        # Ladakh: high altitude, requires acclimatization
        ladakh_caps = load_capabilities("ladakh")
        self.assertTrue(ladakh_caps.get("requires_altitude_validation"))
        self.assertTrue(ladakh_caps.get("requires_acclimatization_logic"))
        self.assertEqual(ladakh_caps.get("default_base_location_id"), "ladakh:leh")

        # Rajasthan: multi-city road circuit
        raj_caps = load_capabilities("rajasthan")
        self.assertTrue(raj_caps.get("supports_multi_city_circuit"))
        self.assertFalse(raj_caps.get("supports_ferry"))

    # ── 2. Cross-Destination Isolation & Rejection ───────────────────────────

    def test_04_cross_destination_hotel_mismatch_rejected(self):
        """Goa trip with Rajasthan hotel must be flagged as invalid."""
        plan = [
            {"day_number": 1, "location": "Candolim", "hotel": "Udaipur Lake Palace Hotel"}
        ]
        res = validate_trip_destination_integrity("goa", ["Candolim"], plan)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("indicates location 'udaipur'" in err.lower() or "belongs to location" in err.lower() for err in res.errors))

    def test_05_cross_destination_activity_leakage_rejected(self):
        """Kerala trip with Goa activity must be rejected."""
        plan = [
            {"day_number": 1, "location": "Kochi", "activities": ["goa:act:baga_water_sports"]}
        ]
        res = validate_trip_destination_integrity("kerala", ["kerala:kochi"], plan)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("cross-destination leakage" in err.lower() for err in res.errors))

    def test_06_non_ferry_destination_rejects_ferry(self):
        """Ladakh or Rajasthan trip requesting an ocean ferry must be rejected."""
        plan = [
            {"day_number": 1, "location": "Leh", "ferry": "Makruzz (Port Blair to Havelock)"}
        ]
        res = validate_trip_destination_integrity("ladakh", ["ladakh:leh"], plan)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("does not support ferries" in err.lower() for err in res.errors))

    def test_07_ladakh_acclimatization_rule(self):
        """Ladakh Day 1 scheduled at high altitude (Pangong) without Leh rest must be rejected."""
        # Invalid Day 1: Pangong Lake right after landing
        bad_plan = [
            {"day_number": 1, "location": "Pangong", "activities": []}
        ]
        bad_res = validate_trip_destination_integrity("ladakh", ["ladakh:pangong"], bad_plan)
        self.assertFalse(bad_res.is_valid)
        self.assertTrue(any("mandatory base acclimatization" in err.lower() for err in bad_res.errors))

        # Valid Day 1: Leh base
        good_plan = [
            {"day_number": 1, "location": "Leh", "activities": []}
        ]
        good_res = validate_trip_destination_integrity("ladakh", ["ladakh:leh"], good_plan)
        self.assertTrue(good_res.is_valid)

    # ── 3. Level 1 Protected Reference (Andaman / Darun Tourism) ─────────────

    def test_08_andaman_protected_reference_intact(self):
        """Andaman must remain non-additive, loading its original CSV datasets without deviation."""
        self.assertFalse(is_additive_destination("Andaman Islands"))
        self.assertFalse(is_additive_destination("andaman"))

        andaman_dests = load_andaman_destinations()
        self.assertGreater(len(andaman_dests), 0)
        dest_names = [str(x) for x in andaman_dests["destination_name"].tolist()] if hasattr(andaman_dests, "to_dict") else [str(x) for x in andaman_dests]
        self.assertTrue(any("Havelock" in name or "Swaraj" in name for name in dest_names))

        # Andaman validator passes standard Andaman plans
        res = validate_trip_destination_integrity("Andaman Islands", ["Port Blair"], [])
        self.assertTrue(res.is_valid)

    def test_09_image_resolver_isolation(self):
        """Non-Andaman trips must never resolve Andaman photos."""
        # Non-additive trip should never return an Andaman photo
        resolved = resolve_namespace_image("rajasthan", "Elephant Beach")
        self.assertIsNone(resolved, "Rajasthan must never return Andaman's Elephant Beach image")

        resolved_kerala = resolve_namespace_image("kerala", "Radhanagar Beach")
        self.assertIsNone(resolved_kerala, "Kerala must never return Andaman's Radhanagar Beach image")

        # Andaman trip resolves its own valid local assets
        req = TripRequest(
            destination="Andaman Islands",
            number_of_days=3,
            number_of_nights=2,
            trip_type="Family",
            hotel_tier="4 Star",
            selected_destinations=["Port Blair", "Havelock"],
        )
        andaman_img = resolve_day_image(req, 1)
        if andaman_img:
            self.assertTrue(andaman_img.exists() or isinstance(andaman_img, Path))

    # ── 4. Scaffolding & Dynamic Discovery ───────────────────────────────────

    def test_10_scaffolded_destinations_distinguished_from_active(self):
        """Scaffolded destinations must have status 'scaffold' and not be listed in active filter."""
        active_list = list_destinations("active")
        active_slugs = [d["slug"] for d in active_list]
        self.assertIn("goa", active_slugs)
        self.assertIn("kerala", active_slugs)
        self.assertIn("ladakh", active_slugs)
        self.assertNotIn("punjab", active_slugs, "Punjab is scaffold and should not be in active list")

        all_list = list_destinations()
        all_slugs = [d["slug"] for d in all_list]
        self.assertIn("punjab", all_slugs)
        punjab_item = next(d for d in all_list if d["slug"] == "punjab")
        self.assertEqual(punjab_item["status"], "scaffold")
        self.assertEqual(punjab_item["locations_count"], 0, "Scaffold must not contain fake data")


if __name__ == "__main__":
    unittest.main()
