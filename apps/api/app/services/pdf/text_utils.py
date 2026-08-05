"""
Text utility functions: splitting, deduplication, formatting, escaping.
"""
import re


def split_values(text: object) -> list[str]:
    """Split a string or list into a cleaned list of non-empty values."""
    if not text:
        return []
    if isinstance(text, list):
        return [str(item).strip() for item in text if str(item).strip() and str(item).strip().lower() != "none"]
    values: list[str] = []
    for chunk in re.split(r"[,\n]", str(text or "")):
        cleaned = chunk.strip()
        if not cleaned or cleaned.lower() == "none":
            continue
        values.append(cleaned)
    return values


def unique_values(values: list[str]) -> list[str]:
    """Return a list with duplicates removed, preserving order."""
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            unique.append(cleaned)
            seen.add(key)
    return unique


def format_list(values: list[str], fallback: str = "As selected") -> str:
    """Format a list as a human-readable string."""
    items = unique_values(values)
    if not items:
        return fallback
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def format_list_short(values: list[str], max_len: int = 40, fallback: str = "As selected") -> str:
    """Format a list, truncating with '+ X more' if it exceeds max length."""
    items = unique_values(values)
    if not items:
        return fallback
    
    result = items[0]
    for i in range(1, len(items)):
        next_result = f"{result}, {items[i]}"
        if len(next_result) > max_len:
            return f"{result} & {len(items) - i} more"
        result = next_result
        
    if len(items) > 1:
        return f"{', '.join(items[:-1])} and {items[-1]}"
    return items[0]



def clean_destination_label(text: str) -> str:
    cleaned = re.sub(r"\s*\([^)]*\)", "", str(text or "")).strip()
    return re.sub(r"\s+", " ", cleaned)


def normalize_destination_key(text: str) -> str:
    return clean_destination_label(text).lower()


def escape_text(text: str) -> str:
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sanitize_itinerary_text(itinerary_text: str) -> str:
    import json
    try:
        cleaned = (itinerary_text or "").strip()
        match = re.search(r"\{.*\}\s*$", cleaned, re.DOTALL)
        json_candidate = match.group(0).strip() if match else cleaned
        json.loads(json_candidate, strict=False)
        return itinerary_text
    except Exception:
        pass

    cleaned_lines = []
    for line in itinerary_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = re.sub(r"[*_`#>\[\]]", "", cleaned)
        cleaned = re.sub(r"^\s*[-•]\s*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:")
        if cleaned:
            cleaned_lines.append(cleaned)
    return "\n".join(cleaned_lines)


def extract_trip_title(itinerary_text: str, destination: str) -> str:
    import json
    try:
        cleaned = (itinerary_text or "").strip()
        match = re.search(r"\{.*\}\s*$", cleaned, re.DOTALL)
        json_candidate = match.group(0).strip() if match else cleaned
        json.loads(json_candidate, strict=False)
        return f"{destination} Journey"
    except Exception:
        pass

    for line in itinerary_text.splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.lower().startswith("day "):
            return cleaned
    return f"{destination} Journey"


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", str(text or "")) if part.strip()])


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", str(text or "")))


def ensure_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned
