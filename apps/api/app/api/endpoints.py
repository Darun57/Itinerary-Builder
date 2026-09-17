import traceback
import os
from fastapi import APIRouter, HTTPException, Response, Header
from pydantic import BaseModel

from app.schemas.trip import TripRequest
from app.services import recommendations
from app.services import google_service
from app.services import pdf_service
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
def list_hotels():
    """Return all hotels in the database (for management / UI browse)."""
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
    return _recommend(recommendations.recommend_activities, request)


@router.post("/recommendations/ferries")
def get_ferry_recommendations(request: TripRequest):
    return _recommend(recommendations.recommend_ferries, request)


@router.post("/recommendations/destinations")
def get_destination_recommendations(request: TripRequest):
    return _recommend(recommendations.recommend_destinations, request)


@router.get("/data/destinations")
def get_all_destinations():
    return _safe_records(load_destinations())


@router.get("/data/activities")
def get_all_activities():
    return _safe_records(load_activities())


@router.get("/data/ferries")
def get_all_ferries():
    return _safe_records(load_ferries())

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
