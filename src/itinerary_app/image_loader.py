from pathlib import Path
import re


IMAGE_ROOT = Path(__file__).resolve().parents[2] / "assets" / "images"
DEFAULT_COVER_IMAGE = IMAGE_ROOT / "default_cover" / "cover.jpg"
DEFAULT_FALLBACK_IMAGE = IMAGE_ROOT / "default" / "default.jpg"
DESTINATION_IMAGE_DIRS = {
    "port blair": "port_blair",
    "swaraj dweep": "swaraj_dweep",
    "havelock": "swaraj_dweep",
    "havelock island": "swaraj_dweep",
    "shaheed dweep": "shaheed_dweep",
    "neil": "shaheed_dweep",
    "neil island": "shaheed_dweep",
    "baratang": "baratang",
    "diglipur": "diglipur",
    "rangat": "rangat",
    "mayabunder": "mayabunder",
    "little andaman": "little_andaman",
    "ross island": "ross_island",
    "ross island (netaji subhash chandra bose island)": "ross_island",
    "netaji subhash chandra bose island": "ross_island",
    "north bay": "north_bay",
    "north bay island": "north_bay",
    "jolly buoy": "jolly_buoy",
    "jolly buoy island": "jolly_buoy",
    "red skin": "red_skin",
    "red skin island": "red_skin",
    "chidiya tapu": "chidiya_tapu",
    "wandoor": "wandoor",
    "wandoor beach": "wandoor",
    "cinque island": "cinque_island",
    "long island": "long_island",
    "barren island": "barren_island",
    "barren island cruise": "barren_island",
    "interview island": "interview_island",
    "cellular jail": "cellular_jail",
    "light and sound show": "cellular_jail",
    "radhanagar beach": "radhanagar_beach",
    "elephant beach": "elephant_beach",
    "kala pathar beach": "kala_pathar",
    "kala pathar": "kala_pathar",
    "bharatpur beach": "bharatpur_beach",
    "laxmanpur beach": "laxmanpur_beach",
    "natural bridge": "natural_bridge",
    "sitapur beach": "sitapur_beach",
    "corbyn's cove beach": "corbyn_cove",
    "corbyn cove beach": "corbyn_cove",
    "corbyn cove": "corbyn_cove",
    "flag point": "flag_point",
    "marina park": "marina_park",
    "anthropological museum": "anthropological_museum",
    "samudrika marine museum": "samudrika_museum",
    "chatham saw mill": "chatham_sawmill",
    "fisheries museum": "fisheries_museum",
    "jogger's park": "joggers_park",
    "joggers park": "joggers_park",
    "limestone cave": "limestone_cave",
    "mud volcano": "mud_volcano",
    "mangrove boat ride": "mangrove_boat_ride",
    "ross & smith sandbar": "ross_smith_islands",
    "ross and smith islands": "ross_smith_islands",
    "saddle peak trek": "saddle_peak",
    "kalipur beach": "kalipur_beach",
}
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
POINTER_FILENAMES = (".gitkeep", ".txt", ".list")


def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _candidate_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    files: list[Path] = []
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return files


def _resolve_pointer_text(text: str) -> Path | None:
    cleaned = str(text or "").strip().strip('"').strip("'")
    if not cleaned:
        return None
    candidate = Path(cleaned)
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
        return candidate
    candidate = (IMAGE_ROOT / cleaned).resolve()
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
        return candidate
    candidate = (Path(__file__).resolve().parents[2] / cleaned).resolve()
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS:
        return candidate
    return None


def _pointer_candidates(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    candidates: list[Path] = []
    for filename in POINTER_FILENAMES:
        pointer_file = directory / filename
        if pointer_file.exists() and pointer_file.is_file():
            try:
                for line in pointer_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                    resolved = _resolve_pointer_text(line)
                    if resolved and resolved not in candidates:
                        candidates.append(resolved)
            except Exception:
                continue
    return candidates


def _collect_images(directory: Path) -> list[Path]:
    images = _candidate_files(directory)
    if images:
        return images
    return _pointer_candidates(directory)


def _destination_folder(destination: str) -> Path | None:
    normalized_destination = _normalized_text(destination)
    for key, folder_name in DESTINATION_IMAGE_DIRS.items():
        if key in normalized_destination:
            return IMAGE_ROOT / folder_name
    return None


def get_cover_image_path() -> Path | None:
    if DEFAULT_COVER_IMAGE.exists():
        return DEFAULT_COVER_IMAGE
    if DEFAULT_FALLBACK_IMAGE.exists():
        return DEFAULT_FALLBACK_IMAGE
    default_folder = IMAGE_ROOT / "default_cover"
    candidates = _collect_images(default_folder)
    if candidates:
        return candidates[0]
    default_folder = IMAGE_ROOT / "default"
    candidates = _collect_images(default_folder)
    if candidates:
        return candidates[0]
    return None


def get_fallback_image_path() -> Path | None:
    if DEFAULT_FALLBACK_IMAGE.exists():
        return DEFAULT_FALLBACK_IMAGE
    default_folder = IMAGE_ROOT / "default"
    candidates = _collect_images(default_folder)
    if candidates:
        return candidates[0]
    return None


def get_destination_image_paths(destination: str) -> list[Path]:
    folder = _destination_folder(destination)
    if folder is None:
        return []
    return _collect_images(folder)


def get_destination_image_path(destination: str) -> Path | None:
    paths = get_destination_image_paths(destination)
    return paths[0] if paths else get_fallback_image_path()
