"""Additive destination registry for Velqairn.

This module is intentionally isolated from the existing Darun/Andaman data loader.
It resolves destination-scoped JSON data without changing the protected running path.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DESTINATION_ROOT = PROJECT_ROOT / "velqairn_destination_data"

SUPPORTED = {
    "rajasthan": "rajasthan",
    "jammu-and-kashmir": "jammu_and_kashmir",
    "jammu_kashmir": "jammu_and_kashmir",
}


def normalize_region(region: str) -> str:
    key = str(region or "").strip().lower().replace(" ", "-")
    if key not in SUPPORTED:
        raise ValueError(f"Unsupported destination region: {region}")
    return SUPPORTED[key]


def _load(region: str, collection: str, filename: str) -> list[dict[str, Any]]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / collection / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return payload


def load_destinations(region: str) -> list[dict[str, Any]]:
    return _load(region, "destinations", "locations.json")


def load_attractions(region: str) -> list[dict[str, Any]]:
    return _load(region, "attractions", "attractions.json")


def load_activities(region: str) -> list[dict[str, Any]]:
    return _load(region, "activities", "activities.json")


def load_movements(region: str) -> list[dict[str, Any]]:
    return _load(region, "movements", "movements.json")


def load_day_plans(region: str) -> list[dict[str, Any]]:
    return _load(region, "day_plans", "day_plans.json")


def load_config(region: str) -> dict[str, Any]:
    folder = normalize_region(region)
    path = DESTINATION_ROOT / folder / "config" / "destination.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_destination_context(region: str) -> dict[str, Any]:
    """Return a destination-scoped knowledge bundle for the AI/planner layer."""
    return {
        "config": load_config(region),
        "destinations": load_destinations(region),
        "attractions": load_attractions(region),
        "activities": load_activities(region),
        "movements": load_movements(region),
        "day_plans": load_day_plans(region),
    }
