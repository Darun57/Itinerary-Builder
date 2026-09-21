from pathlib import Path
import re

IMAGE_ROOT = Path(__file__).resolve().parents[4] / "assets" / "images"
DEFAULT_COVER_IMAGE = IMAGE_ROOT / "port_blair" / "port blair.jpg"

DESTINATION_IMAGE_DIRS = {
    # Port Blair & South Andaman
    "port blair": ["port_blair"],
    "cellular jail": ["port_blair"],
    "chidiya tapu": ["port_blair"],
    "corbyn": ["port_blair"],
    "ross island": ["ross_island"],
    "rose island": ["ross_island"],
    "north bay": ["north_bay"],
    "jolly buoy": ["jolly_buoy"],
    "red skin": ["red_skin"],
    "wandoor": ["wandoor"],

    # Havelock Island / Swaraj Dweep
    "havelock": ["swaraj_dweep", "radhanagar_beach", "elephant_beach"],
    "swaraj dweep": ["swaraj_dweep", "radhanagar_beach", "elephant_beach"],
    "radhanagar": ["radhanagar_beach", "swaraj_dweep"],
    "elephant beach": ["elephant_beach", "swaraj_dweep"],
    "kalapathar": ["swaraj_dweep"],
    "kala pathar": ["swaraj_dweep"],

    # Neil Island / Shaheed Dweep
    "neil island": ["shaheed_dweep"],
    "neil": ["shaheed_dweep"],
    "shaheed dweep": ["shaheed_dweep"],
    "bharatpur": ["shaheed_dweep"],
    "natural bridge": ["shaheed_dweep"],
    "laxmanpur": ["shaheed_dweep"],
    "sitapur": ["shaheed_dweep"],

    # Middle & North Andaman
    "baratang": ["port_blair"],
    "limestone caves": ["port_blair"],
    "diglipur": ["diglipur"],
    "ross and smith": ["diglipur"],
    "saddle peak": ["diglipur"],
    "long island": ["long_island"],
    "little andaman": ["little_andaman"],
    "rangat": ["rangat"],
    "mayabunder": ["mayabunder"],

    # Departure
    "departure": ["departure"],
    "airport": ["departure"],
}
SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
POINTER_FILENAMES = (".gitkeep", ".txt", ".list")

def _normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()

def _candidate_files(directory: Path) -> list[Path]:
    if not directory.exists(): return []
    return [p for p in sorted(directory.iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]

def _resolve_pointer_text(text: str) -> Path | None:
    cleaned = str(text or "").strip().strip('"').strip("'")
    if not cleaned: return None
    candidate = Path(cleaned)
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS: return candidate
    candidate = (IMAGE_ROOT / cleaned).resolve()
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS: return candidate
    candidate = (Path(__file__).resolve().parents[4] / cleaned).resolve()
    if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in SUPPORTED_EXTENSIONS: return candidate
    return None

def _pointer_candidates(directory: Path) -> list[Path]:
    if not directory.exists(): return []
    out=[]
    for filename in POINTER_FILENAMES:
        pointer_file=directory/filename
        if pointer_file.exists() and pointer_file.is_file():
            try:
                for line in pointer_file.read_text(encoding="utf-8",errors="ignore").splitlines():
                    resolved=_resolve_pointer_text(line)
                    if resolved and resolved not in out: out.append(resolved)
            except Exception: pass
    return out

def _collect_images(directory: Path) -> list[Path]:
    imgs=_candidate_files(directory)
    return imgs if imgs else _pointer_candidates(directory)

def _destination_folders(destination: str) -> list[Path]:
    normalized_destination=_normalized_text(destination)
    folders = []
    for key, folder_names in DESTINATION_IMAGE_DIRS.items():
        if key in normalized_destination:
            for f in folder_names:
                p = IMAGE_ROOT / f
                if p.exists() and p not in folders:
                    folders.append(p)
    return folders

def get_cover_image_path() -> Path | None:
    primary = IMAGE_ROOT / "default_cover" / "cover.jpg"
    if primary.exists() and primary.is_file():
        return primary
    candidates = [
        IMAGE_ROOT / "default_cover" / "cover.jpg",
        IMAGE_ROOT / "port_blair" / "radhanagar beach.jpg",
        IMAGE_ROOT / "swaraj_dweep" / "radhanagar beach.jpg",
        IMAGE_ROOT / "port_blair" / "port blair.jpg",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return get_fallback_image_path()

def get_fallback_image_path() -> Path | None:
    candidates = [
        IMAGE_ROOT / "swaraj_dweep" / "radhanagar beach.jpg",
        IMAGE_ROOT / "port_blair" / "port blair.jpg",
        IMAGE_ROOT / "shaheed_dweep" / "neil island.jpg",
        IMAGE_ROOT / "elephant_beach" / "elephant beach.jpg",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    all_imgs = [p for p in IMAGE_ROOT.glob("*/*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return all_imgs[0] if all_imgs else None

def get_destination_image_paths(destination: str) -> list[Path]:
    folders = _destination_folders(destination)
    all_imgs = []
    for folder in folders:
        imgs = _collect_images(folder)
        for img in imgs:
            if img not in all_imgs:
                all_imgs.append(img)
    return all_imgs

def get_destination_image_path(destination: str) -> Path | None:
    paths = get_destination_image_paths(destination)
    return paths[0] if paths else get_fallback_image_path()
