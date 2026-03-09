"""
PDF Generation and Manipulation Client — Stub for MVP.

Planned capabilities:
- HTML-to-PDF rendering
- Structured report generation from sections
- PDF merging and splitting
- Watermark application
- Text extraction from PDF pages
"""

from typing import Dict, Any, Optional, List


class PDFClient:
    """PDF generation and manipulation client (stub — not yet implemented)."""

    def __init__(self):
        pass

    async def generate_from_html(
        self,
        html_content: str,
        output_path: Optional[str] = None,
        page_size: str = "A4",
    ) -> bytes:
        raise NotImplementedError("PDF generate_from_html not yet implemented")

    async def generate_report(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        output_path: Optional[str] = None,
    ) -> bytes:
        raise NotImplementedError("PDF generate_report not yet implemented")

    async def merge(
        self,
        pdf_paths: List[str],
        output_path: Optional[str] = None,
    ) -> bytes:
        raise NotImplementedError("PDF merge not yet implemented")

    async def split(
        self, pdf_path: str, page_ranges: List[str]
    ) -> List[bytes]:
        raise NotImplementedError("PDF split not yet implemented")

    async def add_watermark(
        self,
        pdf_path: str,
        watermark_text: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        raise NotImplementedError("PDF add_watermark not yet implemented")

    async def extract_text(
        self, pdf_path: str, pages: Optional[str] = None
    ) -> str:
        raise NotImplementedError("PDF extract_text not yet implemented")
