"""
Backward-compatibility shim.

The full implementation has been refactored into ``app.services.pdf``.
This module re-exports the public API so that existing callers require no changes.
"""
from app.services.pdf import generate_luxury_pdf  # noqa: F401

__all__ = ["generate_luxury_pdf"]
