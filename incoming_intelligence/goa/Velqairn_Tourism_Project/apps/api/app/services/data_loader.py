from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data"

HOTEL_COLUMNS = [
    "hotel_id",
    "hotel_name",
    "location",
    "category",
    "room_type",
    "description",
    "availability_status",
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
    except ParserError:
        try:
            frame = pd.read_csv(path, engine="python", on_bad_lines="skip")
        except (EmptyDataError, ParserError, UnicodeDecodeError, OSError) as error:
            raise ValueError(f"Could not load {path}: {error}") from error
    except (UnicodeDecodeError, OSError) as error:
        raise ValueError(f"Could not load {path}: {error}") from error

    missing_columns = [column for column in expected_columns if column not in frame.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"{path} is missing required columns: {missing_text}")

    available_columns = expected_columns + [column for column in optional_columns if column in frame.columns]
    return frame[available_columns]


def load_hotels() -> pd.DataFrame:
    base_required = ["hotel_id", "hotel_name", "location", "category", "description"]
    _OPTIONAL = ["room_type", "availability_status"]
    frame = _load_csv_with_optional("hotels.csv", base_required, _OPTIONAL)
    if "availability_status" not in frame.columns:
        frame["availability_status"] = "Available"
    if "room_type" not in frame.columns:
        frame["room_type"] = ""
    frame["availability_status"] = frame["availability_status"].fillna("Available")
    frame["room_type"] = frame["room_type"].fillna("")
    frame = frame.drop_duplicates(subset=["hotel_id"])
    return frame[HOTEL_COLUMNS]


def _next_hotel_id(location: str) -> str:
    """Generate the next sequential Goa hotel_id."""
    try:
        existing = load_hotels()
        pattern = "HTL-GOA-"
        matched = existing["hotel_id"].astype(str).str.startswith(pattern)
        if matched.any():
            nums = (
                existing.loc[matched, "hotel_id"]
                .str.replace(pattern, "", regex=False)
                .str.extract(r"(\d+)")
                .dropna()[0]
                .astype(int)
            )
            next_num = int(nums.max()) + 1 if len(nums) else 1
        else:
            next_num = 1
    except Exception:
        next_num = 1
    return f"HTL-GOA-{next_num:03d}"


def append_hotel(hotel: dict) -> dict:
    """Validate and append a new hotel row to data/hotels.csv. Returns the saved hotel dict."""
    required = ["hotel_name", "location", "category"]
    for field in required:
        if not hotel.get(field, "").strip():
            raise ValueError(f"Missing required hotel field: {field}")

    hotel_id = _next_hotel_id(hotel["location"])
    new_row = {
        "hotel_id": hotel_id,
        "hotel_name": hotel["hotel_name"].strip(),
        "location": hotel["location"].strip(),
        "category": hotel["category"].strip(),
        "room_type": hotel.get("room_type", "").strip(),
        "description": hotel.get("description", "").strip(),
        "availability_status": hotel.get("availability_status", "Available").strip(),
    }

    path = DATA_DIR / "hotels.csv"
    new_df = pd.DataFrame([new_row])[HOTEL_COLUMNS]
    if path.exists():
        new_df.to_csv(path, mode="a", header=False, index=False)
    else:
        new_df.to_csv(path, mode="w", header=True, index=False)

    return new_row


def load_activities() -> pd.DataFrame:
    return _load_csv("activities.csv", ACTIVITY_COLUMNS)


def load_ferries() -> pd.DataFrame:
    return _load_csv("ferries.csv", FERRY_COLUMNS)


def load_destinations() -> pd.DataFrame:
    return _load_csv("destinations.csv", DESTINATION_COLUMNS)
