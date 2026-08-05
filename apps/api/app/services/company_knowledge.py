from dataclasses import dataclass

import pandas as pd

from app.services.context_builder import build_company_context
from app.schemas.trip import TripRequest
from app.services.recommendations import (
    recommend_activities,
    recommend_destinations,
    recommend_ferries,
    recommend_hotels,
)


@dataclass(frozen=True)
class RecommendationBundle:
    hotels: pd.DataFrame
    activities: pd.DataFrame
    ferries: pd.DataFrame
    destinations: pd.DataFrame


def build_recommendation_bundle(request: TripRequest) -> RecommendationBundle:
    return RecommendationBundle(
        hotels=recommend_hotels(request),
        activities=recommend_activities(request),
        ferries=recommend_ferries(request),
        destinations=recommend_destinations(request),
    )


def build_company_context_for_request(request: TripRequest) -> str:
    bundle = build_recommendation_bundle(request)
    return build_company_context(
        request=request,
        hotels=bundle.hotels,
        activities=bundle.activities,
        ferries=bundle.ferries,
        destinations=bundle.destinations,
    )
