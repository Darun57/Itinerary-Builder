from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class DestinationRecord(BaseModel):
    id: str
    region: str
    name: str
    type: Literal["city", "town", "resort", "wildlife", "circuit_stop"]
    best_for: list[str] = Field(default_factory=list)
    recommended_nights_min: int = 0
    recommended_nights_max: int = 0
    source_status: str = "seeded"


class AttractionRecord(BaseModel):
    id: str
    destination_id: str
    name: str
    category: str
    suggested_duration_minutes: int
    best_for: list[str] = Field(default_factory=list)
    operational_notes: list[str] = Field(default_factory=list)
    source_status: str = "seeded"


class ActivityRecord(BaseModel):
    id: str
    destination_id: str
    name: str
    category: str
    duration_minutes_min: int
    duration_minutes_max: int
    best_for: list[str] = Field(default_factory=list)
    seasonality: list[str] = Field(default_factory=list)
    booking_required: bool = False
    price_status: Literal["unknown", "supplier_required", "fixed"] = "unknown"
    source_status: str = "seeded"


class MovementRecord(BaseModel):
    id: str
    region: str
    from_destination_id: str
    to_destination_id: str
    mode: str
    estimated_duration_minutes_min: int
    estimated_duration_minutes_max: int
    planning_status: Literal["planning_estimate", "live_verification_required"] = "planning_estimate"
    notes: list[str] = Field(default_factory=list)


class DayPlanTemplate(BaseModel):
    id: str
    region: str
    day_count: int
    nights: int
    sequence: list[dict]
    suitability: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
