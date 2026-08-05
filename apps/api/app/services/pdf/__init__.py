"""
PDF package for Darun Tourism itinerary generation.

Public API:
    generate_luxury_pdf(request, itinerary_text) -> bytes
"""
from app.services.pdf.builder import generate_luxury_pdf

__all__ = ["generate_luxury_pdf"]
