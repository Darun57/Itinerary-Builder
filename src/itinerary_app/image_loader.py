from pathlib import Path
import re


IMAGE_ROOT = Path(__file__).resolve().parents[2] / "assets" / "images"
HOTEL_IMAGE_ROOT = IMAGE_ROOT / "hotels"
DESTINATION_IMAGE_DIRS = {
    "port blair": "port_blair",
    "swaraj dweep": "swaraj_dweep",
    "havelock": "swaraj_dweep",
    "shaheed dweep": "shaheed_dweep",
    "neil": "shaheed_dweep",
    "baratang": "baratang",
}
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")


def _find_first_image(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    for extension in SUPPORTED_EXTENSIONS:
        matches = sorted(directory.glob(f"*{extension}"))
        if matches:
            return matches[0]
        matches = sorted(directory.glob(f"*{extension.upper()}"))
        if matches:
            return matches[0]
    return None


def get_destination_image_path(destination: str) -> Path | None:
    normalized_destination = str(destination or "").strip().lower()
    for key, folder_name in DESTINATION_IMAGE_DIRS.items():
        if key in normalized_destination:
            image_path = _find_first_image(IMAGE_ROOT / folder_name)
            if image_path:
                return image_path
    return _find_first_image(IMAGE_ROOT)


def get_hotel_image_path(hotel_name: str) -> Path | None:
    normalized_name = re.sub(r"[^a-z0-9]+", "_", str(hotel_name or "").strip().lower()).strip("_")
    if not HOTEL_IMAGE_ROOT.exists():
        return None
    for extension in SUPPORTED_EXTENSIONS:
        candidate = HOTEL_IMAGE_ROOT / f"{normalized_name}{extension}"
        if candidate.exists():
            return candidate
    for path in HOTEL_IMAGE_ROOT.glob(f"*{normalized_name}*"):
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return path
    return _find_first_image(HOTEL_IMAGE_ROOT)
