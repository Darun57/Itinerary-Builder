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


def resolve_day_image(request: TripRequest, day_number: int, used_images: set[Path] | None = None, is_final_day: bool = False) -> Path | None:
    if used_images is None:
        used_images = set()
    trip_context = build_trip_context(request)
    day_plan = get_day(trip_context, day_number)
    if day_plan is None:
        return get_fallback_image_path()
    primary_island = get_primary_island(trip_context, day_number)
    attractions = get_day_attractions(trip_context, day_number)
    search_labels = [*attractions[:2], primary_island]
    
    if is_final_day:
        search_labels.insert(0, "departure")
    for label in search_labels:
        if not label:
            continue
        candidates = [p for p in get_destination_image_paths(label) if p not in used_images]
        if candidates:
            selected = random.choice(candidates)
            used_images.add(selected)
            return selected
    fallback = get_fallback_image_path()
    if fallback:
        used_images.add(fallback)
        return fallback
    return None
