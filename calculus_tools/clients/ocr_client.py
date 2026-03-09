"""
OCR (Optical Character Recognition) Client — Stub for MVP.

Planned capabilities:
- Text extraction from images (Tesseract, Google Vision, etc.)
- Structured data extraction (JSON output)
- Table detection and extraction
- PDF text extraction
- Receipt and document parsing
"""

from typing import Dict, Any, Optional, List


class OCRClient:
    """OCR API client (stub — not yet implemented)."""

    def __init__(
        self, provider: str = "tesseract", api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key

    async def extract_text(
        self, image_path: str, language: str = "eng"
    ) -> Dict[str, Any]:
        raise NotImplementedError("OCR extract_text not yet implemented")

    async def extract_structured(
        self, image_path: str, output_format: str = "json"
    ) -> Dict[str, Any]:
        raise NotImplementedError("OCR extract_structured not yet implemented")

    async def extract_tables(
        self, image_path: str
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("OCR extract_tables not yet implemented")

    async def extract_from_pdf(
        self, pdf_path: str, pages: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("OCR extract_from_pdf not yet implemented")

    async def extract_receipts(
        self, image_path: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("OCR extract_receipts not yet implemented")
