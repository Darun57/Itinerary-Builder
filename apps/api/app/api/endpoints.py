import traceback
import os
from fastapi import APIRouter, HTTPException, Response, Header
from pydantic import BaseModel

from typing import Optional
from app.schemas.trip import TripRequest
from app.services import recommendations
from app.services import google_service
from app.services import pdf_service
from app.services import destination_registry
from app.services.destination_registry import is_additive_destination
from app.services.destination_validator import validate_trip_destination_integrity
import pandas as pd
from app.services.data_loader import load_destinations, load_activities, load_ferries, load_hotels, append_hotel

router = APIRouter()


def _safe_records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    import math
    records = df.to_dict(orient="records")
    for row in records:
        for k, v in list(row.items()):
            if v is None or pd.isna(v) or (isinstance(v, float) and math.isnan(v)):
                row[k] = ""
    return records


def _recommend(fn, request: TripRequest):
    """Shared helper: run a recommendation function and return JSON-serialisable records."""
    try:
        return _safe_records(fn(request))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommendations/hotels")
def get_hotel_recommendations(request: TripRequest):
    destination = getattr(request, "destination", "") or ""
    if is_additive_destination(destination):
        # Do not invent hotels; return verified supplier data or empty catalog
        return destination_registry.load_hotels(destination)
    try:
        return _safe_records(recommendations.recommend_hotels(request, for_ui=True))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Hotel CRUD ──────────────────────────────────────────────────────────────

class HotelCreateRequest(BaseModel):
    hotel_name: str
    location: str
    category: str
    room_type: str = ""
    description: str = ""
    availability_status: str = "Available"


@router.get("/hotels")
def list_hotels(region: Optional[str] = None):
    """Return all hotels in the database (for management / UI browse)."""
    if region and is_additive_destination(region):
        return destination_registry.load_hotels(region)
    return _safe_records(load_hotels())


@router.post("/hotels", status_code=201)
def create_hotel(payload: HotelCreateRequest):
    """Append a new hotel to hotels.csv and return the saved row."""
    try:
        saved = append_hotel(payload.model_dump())
        return saved
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommendations/activities")
def get_activity_recommendations(request: TripRequest):
    destination = getattr(request, "destination", "") or ""
    if is_additive_destination(destination):
        return destination_registry.load_activities(destination)
    return _recommend(recommendations.recommend_activities, request)


@router.post("/recommendations/ferries")
def get_ferry_recommendations(request: TripRequest):
    destination = getattr(request, "destination", "") or ""
    if is_additive_destination(destination):
        # Additive destinations (e.g. Rajasthan) do not use Andaman ferries
        return []
    return _recommend(recommendations.recommend_ferries, request)


@router.post("/recommendations/destinations")
def get_destination_recommendations(request: TripRequest):
    destination = getattr(request, "destination", "") or ""
    if is_additive_destination(destination):
        return destination_registry.load_destinations(destination)
    return _recommend(recommendations.recommend_destinations, request)


@router.get("/data/destinations")
def get_all_destinations(region: Optional[str] = None):
    if region and is_additive_destination(region):
        return destination_registry.load_destinations(region)
    return _safe_records(load_destinations())


@router.get("/data/activities")
def get_all_activities(region: Optional[str] = None):
    if region and is_additive_destination(region):
        return destination_registry.load_activities(region)
    return _safe_records(load_activities())


@router.get("/data/ferries")
def get_all_ferries():
    return _safe_records(load_ferries())


# ── Additive Destination Registry Endpoints ─────────────────────────────────

@router.get("/destinations")
def get_destinations(status: Optional[str] = "active"):
    """List all destinations known to Velqairn, including protected Andaman and additive modules."""
    items = []
    # Include Andaman as Level 1 protected running reference
    items.append({
        "slug": "andaman",
        "name": "Andaman Islands",
        "status": "active",
        "tier": "level_1_protected",
        "capabilities": {
            "transport_modes": ["ferry", "road", "speed_boat"],
            "supports_ferry": True,
            "supports_houseboat": False,
            "requires_altitude_validation": False,
            "requires_acclimatization_logic": False,
            "supports_multi_city_circuit": True,
            "seasonality_required": True,
            "default_base_location_id": "Port Blair",
            "typical_circuit_pace": "moderate",
            "recommended_min_days": 4,
            "recommended_max_days": 10,
        },
        "satisfies_contract": True,
    })
    # Add discovered additive modules
    discovered = destination_registry.list_destinations(status_filter=None if status == "all" else status)
    for d in discovered:
        d["tier"] = "level_2_production" if d.get("status") == "active" else "level_3_scaffold"
        items.append(d)
    return items


@router.get("/destinations/{region}/capabilities")
def get_destination_capabilities(region: str):
    clean = str(region or "").strip().lower()
    if clean.startswith("andaman") or not destination_registry.is_additive_destination(region):
        # Andaman fallback capabilities
        return {
            "transport_modes": ["ferry", "road", "speed_boat"],
            "supports_ferry": True,
            "supports_houseboat": False,
            "requires_altitude_validation": False,
            "requires_acclimatization_logic": False,
            "supports_multi_city_circuit": True,
            "seasonality_required": True,
            "default_base_location_id": "Port Blair",
            "typical_circuit_pace": "moderate",
            "recommended_min_days": 4,
            "recommended_max_days": 10,
        }
    try:
        return destination_registry.load_capabilities(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/destinations/{region}/context")
def get_destination_context(region: str):
    try:
        return destination_registry.build_destination_context(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



@router.get("/destinations/{region}/locations")
def get_destination_locations(region: str):
    try:
        return destination_registry.load_destinations(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/destinations/{region}/movements")
def get_destination_movements(region: str):
    try:
        return destination_registry.load_movements(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/destinations/{region}/attractions")
def get_destination_attractions(region: str):
    try:
        return destination_registry.load_attractions(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/destinations/{region}/activities")
def get_destination_activities(region: str):
    try:
        return destination_registry.load_activities(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/destinations/{region}/day_plans")
def get_destination_day_plans(region: str):
    try:
        return destination_registry.load_day_plans(region)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/destinations/validate")
def validate_destination_itinerary(payload: dict):
    region = payload.get("region") or payload.get("destination") or ""
    locations = payload.get("selected_destinations") or payload.get("locations") or []
    daily_plan = payload.get("daily_island_plan") or payload.get("daily_plan") or []
    res = validate_trip_destination_integrity(region, locations, daily_plan)
    return res.model_dump()

import time
@router.get("/test/timeout")
def test_timeout():
    time.sleep(35)
    return {"status": "ok"}



class AIGenerationResponse(BaseModel):
    itinerary_text: str


@router.post("/ai/generate", response_model=AIGenerationResponse)
def generate_ai_itinerary(request: TripRequest, x_api_key: str = Header(None)):
    try:
        api_key = x_api_key or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        text = google_service.generate_itinerary(api_key, model, request)
        return AIGenerationResponse(itinerary_text=text)
    except Exception as exc:
        # NEVER throw an error to the frontend — always return a valid itinerary
        import logging
        logging.getLogger(__name__).warning("AI generation failed (%s). Returning built-in fallback itinerary.", exc)
        fallback_text = google_service._generate_fallback_itinerary(request)
        return AIGenerationResponse(itinerary_text=fallback_text)


class PDFGenerateRequest(BaseModel):
    request: TripRequest
    itinerary_text: str


@router.post("/pdf/generate")
def generate_pdf(payload: PDFGenerateRequest):
    try:
        pdf_bytes = pdf_service.generate_luxury_pdf(payload.request, payload.itinerary_text)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
