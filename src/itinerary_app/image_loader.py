from pathlib import Path


IMAGE_ROOT = Path(__file__).resolve().parents[2] / "assets" / "images"
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
