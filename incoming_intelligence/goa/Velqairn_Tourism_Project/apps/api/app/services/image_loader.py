from pathlib import Path
import re

IMAGE_ROOT = Path(__file__).resolve().parents[4] / "assets" / "images"
DEFAULT_COVER_IMAGE = IMAGE_ROOT / "default_cover" / "cover.jpg"
DEFAULT_FALLBACK_IMAGE = IMAGE_ROOT / "default" / "default.jpg"
DESTINATION_IMAGE_DIRS = {
    "panaji": "panaji",
    "panjim": "panaji",
    "fontainhas": "fontainhas",
    "old goa": "old_goa",
    "basilica of bom jesus": "old_goa",
    "dona paula": "dona_paula",
    "divar island": "divar_island",
    "north goa": "north_goa",
    "candolim": "candolim",
    "calangute": "calangute",
    "baga": "baga",
    "anjuna": "anjuna",
    "vagator": "vagator",
    "chapora": "chapora",
    "chapora fort": "chapora",
    "morjim": "morjim",
    "ashwem": "ashwem",
    "mandrem": "mandrem",
    "arambol": "arambol",
    "aguada": "aguada",
    "fort aguada": "aguada",
    "grand island": "grand_island",
    "bogmalo": "bogmalo",
    "south goa": "south_goa",
    "majorda": "majorda",
    "colva": "colva",
    "benaulim": "benaulim",
    "varca": "varca",
    "cavelossim": "cavelossim",
    "mobor": "mobor",
    "agonda": "agonda",
    "palolem": "palolem",
    "patnem": "patnem",
    "cabo de rama": "cabo_de_rama",
    "netravali": "netravali",
    "dudhsagar": "dudhsagar",
    "collem": "collem",
    "ponda": "ponda",
    "spice plantation": "spice_plantation",
    "assagao": "assagao",
    "siolim": "siolim",
    "tiracol": "tiracol",
    "miramar": "miramar",
    "panaji waterfront": "panaji",
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

def _destination_folder(destination: str) -> Path | None:
    normalized_destination=_normalized_text(destination)
    for key,folder_name in DESTINATION_IMAGE_DIRS.items():
        if key in normalized_destination: return IMAGE_ROOT/folder_name
    return None

def get_cover_image_path() -> Path | None:
    if DEFAULT_COVER_IMAGE.exists(): return DEFAULT_COVER_IMAGE
    candidates=_collect_images(IMAGE_ROOT/"default_cover")
    return candidates[0] if candidates else None

def get_fallback_image_path() -> Path | None:
    if DEFAULT_FALLBACK_IMAGE.exists(): return DEFAULT_FALLBACK_IMAGE
    candidates=_collect_images(IMAGE_ROOT/"default")
    return candidates[0] if candidates else None

def get_destination_image_paths(destination: str) -> list[Path]:
    folder=_destination_folder(destination)
    return [] if folder is None else _collect_images(folder)

def get_destination_image_path(destination: str) -> Path | None:
    paths=get_destination_image_paths(destination)
    return paths[0] if paths else get_fallback_image_path()
