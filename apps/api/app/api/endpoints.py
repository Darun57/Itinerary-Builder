import traceback
import os
from fastapi import APIRouter, HTTPException, Response, Header
from pydantic import BaseModel

from app.schemas.trip import TripRequest
from app.services import recommendations
from app.services import google_service
from app.services import pdf_service
from app.services.data_loader import load_destinations, load_activities, load_ferries

router = APIRouter()


def _recommend(fn, request: TripRequest):
    """Shared helper: run a recommendation function and return JSON-serialisable records."""
    try:
        return fn(request).to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/recommendations/hotels")
def get_hotel_recommendations(request: TripRequest):
    try:
        return recommendations.recommend_hotels(request, for_ui=True).to_dict(orient="records")
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
    return load_destinations().to_dict(orient="records")


@router.get("/data/activities")
def get_all_activities():
    return load_activities().to_dict(orient="records")


@router.get("/data/ferries")
def get_all_ferries():
    return load_ferries().to_dict(orient="records")

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
