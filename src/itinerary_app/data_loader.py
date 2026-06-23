from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

HOTEL_COLUMNS = [
    "hotel_id",
    "hotel_name",
    "location",
    "category",
    "nightly_price",
    "suitable_for",
    "description",
]
ACTIVITY_COLUMNS = [
    "activity_id",
    "activity_name",
    "location",
    "price",
    "duration",
    "category",
    "description",
]
FERRY_COLUMNS = [
    "ferry_id",
    "operator",
    "from_location",
    "to_location",
    "departure_time",
    "arrival_time",
    "duration",
]
DESTINATION_COLUMNS = [
    "destination_name",
    "best_for",
    "description",
    "minimum_days",
    "maximum_days",
]


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _load_csv(filename: str, expected_columns: list[str]) -> pd.DataFrame:
    return _load_csv_with_optional(filename, expected_columns, [])


def _load_csv_with_optional(
    filename: str,
    expected_columns: list[str],
    optional_columns: list[str],
) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return _empty_frame(expected_columns)

    try:
        frame = pd.read_csv(path)
    except EmptyDataError:
        return _empty_frame(expected_columns)
    except (ParserError, UnicodeDecodeError, OSError) as error:
        raise ValueError(f"Could not load {path}: {error}") from error

    missing_columns = [column for column in expected_columns if column not in frame.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"{path} is missing required columns: {missing_text}")

    available_columns = expected_columns + [column for column in optional_columns if column in frame.columns]
    return frame[available_columns]


def load_hotels() -> pd.DataFrame:
    frame = _load_csv_with_optional("hotels.csv", HOTEL_COLUMNS, ["availability_status"])
    if "availability_status" not in frame.columns:
        frame["availability_status"] = "Available"
    return frame[HOTEL_COLUMNS + ["availability_status"]]


def load_activities() -> pd.DataFrame:
    return _load_csv("activities.csv", ACTIVITY_COLUMNS)


def load_ferries() -> pd.DataFrame:
    return _load_csv("ferries.csv", FERRY_COLUMNS)


def load_destinations() -> pd.DataFrame:
    return _load_csv("destinations.csv", DESTINATION_COLUMNS)
