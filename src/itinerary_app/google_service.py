import time

from google import genai
from google.genai import types

from itinerary_app.models import TripRequest
from itinerary_app.prompts import build_fast_prompt_text


REQUEST_TIMEOUT_MS = 45000
MAX_OUTPUT_TOKENS = 900
MODEL_FALLBACK_ORDER = [
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
]
RETRYABLE_ERROR_HINTS = (
    "503",
    "unavailable",
    "high demand",
    "temporarily unavailable",
)


def _raise_friendly_error(error: Exception) -> None:
    error_message = str(error)
    if "API key expired" in error_message:
        raise ValueError(
            "This Google AI Studio API key has expired. Create a new key in AI Studio > API Keys, "
            "paste the new key in the sidebar, and try again."
        ) from error
    if "API_KEY_INVALID" in error_message or "INVALID_ARGUMENT" in error_message:
        raise ValueError(
            "Google rejected this API key. Check that you pasted a current Gemini API key from Google AI Studio."
        ) from error
    if "timed out" in error_message.lower() or "timeout" in error_message.lower():
        raise ValueError("Gemini took too long to respond. Try again, or use a faster Flash model.") from error
    if any(hint in error_message.lower() for hint in RETRYABLE_ERROR_HINTS):
        raise ValueError(
            "Gemini is temporarily busy right now. Please try again in a moment, or switch to a faster Flash model."
        ) from error
    raise error


def _build_client(api_key: str) -> genai.Client:
    return genai.Client(
        api_key=api_key.strip(),
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS, clientArgs={"trust_env": False}),
    )


def _build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=0.35,
        maxOutputTokens=MAX_OUTPUT_TOKENS,
        thinkingConfig=types.ThinkingConfig(
            thinkingLevel=types.ThinkingLevel.MINIMAL,
            includeThoughts=False,
        ),
    )


def _validate_inputs(api_key: str, model: str) -> None:
    if not api_key.strip():
        raise ValueError("Add a Google AI Studio API key before generating an itinerary.")
    if not model.strip():
        raise ValueError("Choose a valid Gemini model before generating an itinerary.")


def _candidate_models(model: str) -> list[str]:
    selected_model = model.strip()
    candidates = [selected_model]
    for fallback_model in MODEL_FALLBACK_ORDER:
        if fallback_model not in candidates:
            candidates.append(fallback_model)
    return candidates


def _is_retryable_error(error: Exception) -> bool:
    error_message = str(error).lower()
    return any(hint in error_message for hint in RETRYABLE_ERROR_HINTS) or "timed out" in error_message or "timeout" in error_message


def _generate_once(client: genai.Client, model: str, request: TripRequest) -> str:
    stream = client.models.generate_content_stream(
        model=model.strip(),
        contents=build_fast_prompt_text(request),
        config=_build_config(),
    )
    parts: list[str] = []
    for chunk in stream:
        if chunk.text:
            parts.append(chunk.text)
    return "".join(parts).strip()


def generate_itinerary_stream(api_key: str, model: str, request: TripRequest):
    content = generate_itinerary(api_key, model, request)
    if content:
        yield content


def generate_itinerary(api_key: str, model: str, request: TripRequest) -> str:
    _validate_inputs(api_key, model)

    client = _build_client(api_key)
    last_error: Exception | None = None
    for candidate_model in _candidate_models(model):
        for attempt in range(1, 3):
            try:
                content = _generate_once(client, candidate_model, request)
                if content:
                    return content
                last_error = ValueError("Gemini returned an empty itinerary.")
            except Exception as error:
                last_error = error
                if attempt < 2 and _is_retryable_error(error):
                    time.sleep(1.25 * attempt)
                    continue
                if _is_retryable_error(error):
                    break
                _raise_friendly_error(error)

    if last_error is not None:
        _raise_friendly_error(last_error)
    raise ValueError("Gemini returned an empty itinerary.")
