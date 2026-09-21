"""
Image resolution for PDF day pages and cover image generation.
"""
import random
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage, ImageDraw

from app.services.image_loader import get_destination_image_paths, get_fallback_image_path
from app.services.trip_context import build_trip_context, get_day, get_day_attractions, get_primary_island
from app.schemas.trip import TripRequest


def build_cover_image() -> BytesIO:
    width, height = 1600, 900
    image = PILImage.new("RGB", (width, height), "#0c1720")
    draw = ImageDraw.Draw(image)
    for index in range(height):
        ratio = index / max(height - 1, 1)
        red = int(12 + (31 - 12) * ratio)
        green = int(23 + (61 - 23) * ratio)
        blue = int(32 + (89 - 32) * ratio)
        draw.line((0, index, width, index), fill=(red, green, blue))
    draw.ellipse((90, 80, 600, 590), fill=(214, 190, 145))
    draw.polygon([(0, 700), (450, 470), (900, 700)], fill=(37, 71, 82))
    draw.polygon([(520, 760), (1040, 430), (1600, 760)], fill=(24, 55, 66))
    draw.rectangle((0, 760, width, height), fill=(9, 33, 40))
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


import hashlib

from app.services.image_loader import (
    IMAGE_ROOT,
    SUPPORTED_EXTENSIONS,
    get_cover_image_path,
    get_destination_image_paths,
    get_fallback_image_path,
)
from app.services.trip_context import build_trip_context, get_day, get_day_attractions, get_primary_island
from app.schemas.trip import TripRequest


def _image_hash(path: Path) -> str:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return str(path.resolve())


def resolve_day_image(request: TripRequest, day_number: int, used_images: set | None = None, is_final_day: bool = False) -> Path | None:
    if used_images is None:
        used_images = set()

    # Seed used_images with cover image so cover photo is never repeated inside days
    cover_path = get_cover_image_path()
    if cover_path and cover_path.exists():
        used_images.add(_image_hash(cover_path))

    trip_context = build_trip_context(request)
    day_plan = get_day(trip_context, day_number)
    primary_island = get_primary_island(trip_context, day_number) if day_plan else ""
    attractions = get_day_attractions(trip_context, day_number) if day_plan else []

    search_labels = []
    if is_final_day:
        search_labels.append("departure")
    if attractions:
        search_labels.extend(attractions)
    if primary_island:
        search_labels.append(primary_island)
    if request.destination:
        search_labels.append(request.destination)

    # Helper to check if image or its hash was already used
    def _is_unused(p: Path) -> bool:
        if p in used_images:
            return False
        h = _image_hash(p)
        return h not in used_images

    def _mark_used(p: Path) -> None:
        used_images.add(p)
        used_images.add(_image_hash(p))

    # 1. First preference: unused image matching specific labels
    for label in search_labels:
        if not label:
            continue
        candidates = [p for p in get_destination_image_paths(label) if _is_unused(p)]
        if candidates:
            selected = candidates[0]
            _mark_used(selected)
            return selected

    # 2. Second preference: ANY unused Andaman landscape photo from IMAGE_ROOT
    all_unused = [
        p for p in sorted(IMAGE_ROOT.glob("*/*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS and _is_unused(p)
    ]
    if all_unused:
        selected = all_unused[0]
        _mark_used(selected)
        return selected

    # 3. Third preference: reliable fallback image
    fallback = get_fallback_image_path()
    if fallback:
        _mark_used(fallback)
        return fallback
    return None
