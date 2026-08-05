"""
Structured Diagnostic & Observability Logging for Itinerary Generation.
"""
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

DIAGNOSTICS_DIR = Path(__file__).resolve().parent.parent / "storage" / "diagnostics"


def _ensure_dir():
    DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)


def log_generation_event(
    generation_id: str,
    prompt_version: str,
    schema_version: str,
    model: str,
    retry_count: int,
    validation_result: dict[str, Any],
    generation_duration_ms: float,
    pdf_render_duration_ms: float = 0.0,
    outcome: str = "PASSED",
) -> Path:
    """Writes structured JSON diagnostic log file."""
    _ensure_dir()
    
    diagnostic_record = {
        "generation_id": generation_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "narrative_schema_version": schema_version,
        "prompt_version": prompt_version,
        "gemini_model": model,
        "retry_count": retry_count,
        "overall_quality_score": validation_result.get("overall_score", 0.0),
        "section_scores": validation_result.get("section_scores", {}),
        "failed_rules": validation_result.get("failed_rules", []),
        "validation_errors": validation_result.get("errors", []),
        "generation_duration_ms": round(generation_duration_ms, 2),
        "pdf_render_duration_ms": round(pdf_render_duration_ms, 2),
        "validation_outcome": outcome,
    }

    log_file = DIAGNOSTICS_DIR / f"{generation_id}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(diagnostic_record, f, indent=2)

    LOGGER.info("Logged generation diagnostic record to %s", log_file)
    return log_file
