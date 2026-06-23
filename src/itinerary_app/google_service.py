from collections.abc import Iterator

from google import genai
from google.genai import types

from itinerary_app.models import TripRequest
from itinerary_app.prompts import build_fast_prompt_text


REQUEST_TIMEOUT_MS = 45000
MAX_OUTPUT_TOKENS = 1100


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
    raise error


def _build_client(api_key: str) -> genai.Client:
    return genai.Client(
        api_key=api_key.strip(),
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
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


def generate_itinerary_stream(api_key: str, model: str, request: TripRequest) -> Iterator[str]:
    _validate_inputs(api_key, model)

    client = _build_client(api_key)
    try:
        stream = client.models.generate_content_stream(
            model=model.strip(),
            contents=build_fast_prompt_text(request),
            config=_build_config(),
        )
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as error:
        _raise_friendly_error(error)


def generate_itinerary(api_key: str, model: str, request: TripRequest) -> str:
    content = "".join(generate_itinerary_stream(api_key, model, request))
    if not content:
        raise ValueError("Gemini returned an empty itinerary.")

    return content.strip()
