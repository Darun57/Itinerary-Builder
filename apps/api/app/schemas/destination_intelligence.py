from __future__ import annotations

from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field


class DestinationRecord(BaseModel):
    id: str
    region: str
    name: str
    type: Literal["city", "town", "resort", "wildlife", "circuit_stop"] = "city"
    best_for: list[str] = Field(default_factory=list)
    recommended_nights_min: int = 0
    recommended_nights_max: int = 0
    source_status: str = "seeded"


class LocationRecord(BaseModel):
    id: str
    destination_id: str
    name: str
    type: str = "city"
    description: str = ""
    source_status: str = "seeded"


class AttractionRecord(BaseModel):
    id: str
    destination_id: str
    name: str
    category: str = "heritage"
    suggested_duration_minutes: int = 60
    best_for: list[str] = Field(default_factory=list)
    operational_notes: list[str] = Field(default_factory=list)
    source_status: str = "seeded"


class ActivityRecord(BaseModel):
    id: str
    destination_id: str
    name: str
    category: str = "sightseeing"
    duration_minutes_min: int = 60
    duration_minutes_max: int = 120
    best_for: list[str] = Field(default_factory=list)
    seasonality: list[str] = Field(default_factory=list)
    booking_required: bool = False
    price_status: Literal["unknown", "supplier_required", "fixed"] = "unknown"
    source_status: str = "seeded"
    notes: list[str] = Field(default_factory=list)


class MovementRecord(BaseModel):
    id: str
    region: str
    from_destination_id: str
    to_destination_id: str
    mode: str = "road"
    estimated_duration_minutes_min: int = 60
    estimated_duration_minutes_max: int = 120
    planning_status: Literal["planning_estimate", "live_verification_required"] = "planning_estimate"
    notes: list[str] = Field(default_factory=list)


class DayPlanTemplate(BaseModel):
    id: str
    region: str
    day_count: int
    nights: int
    sequence: list[dict[str, Any]]
    suitability: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class HotelRecord(BaseModel):
    id: str
    location_id: str
    name: str
    category: str = "Unknown"
    star_rating: Optional[int] = None
    description: str = ""
    status: Literal["known", "unknown", "needs_supplier_data", "needs_verification"] = "needs_supplier_data"


class RoomRecord(BaseModel):
    id: str
    hotel_id: str
    name: str
    capacity: int = 2
    category: str = "Standard"
    status: Literal["known", "unknown", "needs_supplier_data", "needs_verification"] = "needs_supplier_data"


DestinationStatus = Literal[
    "scaffold",
    "seeded",
    "active",
    "needs_verification",
    "disabled",
    "incomplete"
]


class DestinationCapabilities(BaseModel):
    transport_modes: list[str] = Field(default_factory=lambda: ["road"])
    supports_ferry: bool = False
    supports_houseboat: bool = False
    requires_altitude_validation: bool = False
    requires_acclimatization_logic: bool = False
    supports_multi_city_circuit: bool = True
    seasonality_required: bool = True
    default_base_location_id: Optional[str] = None
    typical_circuit_pace: Literal["slow", "moderate", "fast"] = "moderate"
    recommended_min_days: int = 3
    recommended_max_days: int = 14


class UniversalRoom(BaseModel):
    id: str
    hotel_id: str
    name: str
    capacity: int = 2
    category: str = "Standard"
    meal_plans: list[str] = Field(default_factory=lambda: ["CP", "MAP", "EP", "AP"])
    amenities: list[str] = Field(default_factory=list)
    status: Literal["known", "unknown", "needs_supplier_data", "needs_verification"] = "needs_supplier_data"


class UniversalHotel(BaseModel):
    id: str
    location_id: str
    name: str
    category: str = "Standard"
    star_rating: Optional[int] = None
    room_type: str = ""
    amenities: list[str] = Field(default_factory=list)
    rooms: list[UniversalRoom] = Field(default_factory=list)
    description: str = ""
    contract_status: Literal["direct_contract", "aggregator", "uncontracted", "needs_supplier_data"] = "needs_supplier_data"
    status: Literal["known", "unknown", "needs_supplier_data", "needs_verification"] = "needs_supplier_data"


class DestinationContractSummary(BaseModel):
    slug: str
    name: str
    status: DestinationStatus
    has_config: bool
    has_capabilities: bool
    capabilities: Optional[DestinationCapabilities] = None
    locations_count: int = 0
    attractions_count: int = 0
    activities_count: int = 0
    movements_count: int = 0
    day_plans_count: int = 0
    hotels_count: int = 0
    satisfies_contract: bool = False
    missing_requirements: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

