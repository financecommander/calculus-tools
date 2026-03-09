"""OCR (Optical Character Recognition) client — Google Vision, AWS Textract, Tesseract adapters.

Usage::

    client = OCRClient(provider="google", api_key="...")
    result = await client.extract_text("document.png")
    tables = await client.extract_tables("invoice.png")
    receipt = await client.extract_receipts("receipt.jpg")
    await client.close()
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OCRClient:
    """Async OCR client supporting Google Vision, AWS Textract, and local Tesseract."""

    def __init__(self, provider: str = "google", api_key: str = "", region: str = "us-east-1") -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        self.region = region
        if self.provider == "google":
            self._client = httpx.AsyncClient(
                base_url="https://vision.googleapis.com/v1",
                timeout=30.0,
            )
        elif self.provider == "aws":
            self._client = httpx.AsyncClient(
                base_url=f"https://textract.{region}.amazonaws.com",
                timeout=60.0,
            )
        else:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _encode_image(path: str) -> str:
        return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

    async def extract_text(self, image_path: str, language: str = "eng") -> dict[str, Any]:
        """Extract text from an image."""
        if self.provider == "google":
            b64 = self._encode_image(image_path)
            resp = await self._client.post(f"/images:annotate?key={self.api_key}", json={
                "requests": [{"image": {"content": b64}, "features": [{"type": "TEXT_DETECTION"}], "imageContext": {"languageHints": [language]}}]
            })
            resp.raise_for_status()
            data = resp.json().get("responses", [{}])[0]
            annotations = data.get("textAnnotations", [])
            full_text = annotations[0].get("description", "") if annotations else ""
            blocks = [{"text": a.get("description", ""), "bounds": a.get("boundingPoly", {})} for a in annotations[1:]]
            return {"text": full_text, "blocks": blocks, "language": data.get("fullTextAnnotation", {}).get("pages", [{}])[0].get("property", {}).get("detectedLanguages", []), "confidence": 1.0}
        elif self.provider == "aws":
            image_bytes = Path(image_path).read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            resp = await self._client.post("/", headers={"Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "Textract.DetectDocumentText"}, json={"Document": {"Bytes": b64}})
            resp.raise_for_status()
            data = resp.json()
            lines = [b for b in data.get("Blocks", []) if b.get("BlockType") == "LINE"]
            full_text = "\n".join(line.get("Text", "") for line in lines)
            return {"text": full_text, "blocks": [{"text": line.get("Text", ""), "confidence": line.get("Confidence", 0) / 100, "bounds": line.get("Geometry", {})} for line in lines]}
        elif self.provider == "tesseract":
            return self._tesseract_extract(image_path, language)
        return {"text": "", "blocks": []}

    async def extract_structured(self, image_path: str, output_format: str = "json") -> dict[str, Any]:
        """Extract structured data (key-value pairs, forms) from a document image."""
        if self.provider == "google":
            b64 = self._encode_image(image_path)
            resp = await self._client.post(f"/images:annotate?key={self.api_key}", json={
                "requests": [{"image": {"content": b64}, "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]}]
            })
            resp.raise_for_status()
            data = resp.json().get("responses", [{}])[0]
            full_annotation = data.get("fullTextAnnotation", {})
            return {"text": full_annotation.get("text", ""), "pages": full_annotation.get("pages", []), "format": output_format}
        elif self.provider == "aws":
            image_bytes = Path(image_path).read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            resp = await self._client.post("/", headers={"Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "Textract.AnalyzeDocument"}, json={"Document": {"Bytes": b64}, "FeatureTypes": ["FORMS", "TABLES"]})
            resp.raise_for_status()
            data = resp.json()
            key_values: dict[str, str] = {}
            blocks = {b["Id"]: b for b in data.get("Blocks", []) if "Id" in b}
            for block in data.get("Blocks", []):
                if block.get("BlockType") == "KEY_VALUE_SET" and "KEY" in block.get("EntityTypes", []):
                    key_text = " ".join(
                        blocks.get(r["Id"], {}).get("Text", "")
                        for r in block.get("Relationships", [{}])[0].get("Ids", [])
                        if r.get("Id") in blocks
                    ) if block.get("Relationships") else ""
                    val_block = next((r for r in block.get("Relationships", []) if r.get("Type") == "VALUE"), None)
                    val_text = ""
                    if val_block:
                        for vid in val_block.get("Ids", []):
                            vb = blocks.get(vid, {})
                            val_text += vb.get("Text", "")
                    key_values[key_text] = val_text
            return {"key_values": key_values, "raw_blocks": len(data.get("Blocks", []))}
        return {}

    async def extract_tables(self, image_path: str) -> list[dict[str, Any]]:
        """Extract tables from a document image."""
        if self.provider == "google":
            result = await self.extract_structured(image_path)
            return [{"text": result.get("text", ""), "note": "Google Vision returns full text; use AWS Textract for structured tables"}]
        elif self.provider == "aws":
            image_bytes = Path(image_path).read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            resp = await self._client.post("/", headers={"Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "Textract.AnalyzeDocument"}, json={"Document": {"Bytes": b64}, "FeatureTypes": ["TABLES"]})
            resp.raise_for_status()
            data = resp.json()
            tables = []
            all_blocks = data.get("Blocks", [])
            table_blocks = [b for b in all_blocks if b.get("BlockType") == "TABLE"]
            for tb in table_blocks:
                cells = []
                for rel in tb.get("Relationships", []):
                    if rel.get("Type") == "CHILD":
                        for cid in rel.get("Ids", []):
                            cell = next((b for b in all_blocks if b.get("Id") == cid and b.get("BlockType") == "CELL"), None)
                            if cell:
                                cells.append({"row": cell.get("RowIndex", 0), "col": cell.get("ColumnIndex", 0), "text": cell.get("Text", ""), "confidence": cell.get("Confidence", 0)})
                tables.append({"cells": cells, "row_count": max((c["row"] for c in cells), default=0), "col_count": max((c["col"] for c in cells), default=0)})
            return tables
        return []

    async def extract_from_pdf(self, pdf_path: str, pages: str | None = None) -> dict[str, Any]:
        """Extract text from PDF pages using OCR."""
        # For PDF OCR, we need to convert pages to images first
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = reader.pages[0].extract_text() if reader.pages else ""
            return {"text": text, "page_count": len(reader.pages), "method": "pypdf_text_extraction"}
        except ImportError:
            pass
        return {"text": "", "error": "pypdf not available for PDF text extraction"}

    async def extract_receipts(self, image_path: str) -> dict[str, Any]:
        """Extract receipt data (merchant, total, items, date)."""
        if self.provider == "aws":
            image_bytes = Path(image_path).read_bytes()
            b64 = base64.b64encode(image_bytes).decode()
            resp = await self._client.post("/", headers={"Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "Textract.AnalyzeExpense"}, json={"Document": {"Bytes": b64}})
            resp.raise_for_status()
            data = resp.json()
            expenses = data.get("ExpenseDocuments", [{}])
            if expenses:
                summary = expenses[0].get("SummaryFields", [])
                return {f.get("Type", {}).get("Text", "unknown"): f.get("ValueDetection", {}).get("Text", "") for f in summary}
            return {}
        # For Google, fall back to text extraction + parsing
        result = await self.extract_text(image_path)
        return {"raw_text": result.get("text", ""), "note": "Parse receipt fields from raw text"}

    @staticmethod
    def _tesseract_extract(image_path: str, language: str) -> dict[str, Any]:
        """Local Tesseract OCR extraction."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=language)
            data = pytesseract.image_to_data(img, lang=language, output_type=pytesseract.Output.DICT)
            blocks = [{"text": data["text"][i], "confidence": data["conf"][i], "x": data["left"][i], "y": data["top"][i], "w": data["width"][i], "h": data["height"][i]} for i in range(len(data["text"])) if data["text"][i].strip()]
            return {"text": text, "blocks": blocks, "engine": "tesseract"}
        except ImportError:
            return {"text": "", "error": "pytesseract not installed. Install with: pip install pytesseract Pillow"}
