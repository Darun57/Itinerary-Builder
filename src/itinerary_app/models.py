from dataclasses import dataclass


@dataclass(frozen=True)
class TripRequest:
    customer_name: str
    destination: str
    number_of_nights: int
    number_of_days: int
    trip_type: str
    budget_category: str
    number_of_adults: int
    number_of_children: int
    special_requests: str

