"""Image analysis client — Google Vision, AWS Rekognition, OpenAI Vision adapters.

Usage::

    client = VisionClient(provider="openai", api_key="sk-...")
    result = await client.analyze("path/to/image.jpg", features=["labels", "text", "objects"])
    await client.close()
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class VisionClient:
    """Async image analysis client supporting multiple providers."""

    def __init__(
        self,
        provider: str = "openai",
        api_key: str = "",
        region: str = "us-east-1",
    ) -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        self.region = region
        if self.provider == "openai":
            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=60.0,
            )
        elif self.provider == "google":
            self._client = httpx.AsyncClient(
                base_url="https://vision.googleapis.com/v1",
                timeout=30.0,
            )
        elif self.provider == "aws":
            self._client = httpx.AsyncClient(
                base_url=f"https://rekognition.{region}.amazonaws.com",
                timeout=30.0,
            )
        else:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def _encode_image(image_path: str) -> str:
        return base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")

    @staticmethod
    def _image_mime_type(path: str) -> str:
        ext = Path(path).suffix.lower()
        return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext.lstrip("."), "image/jpeg")

    async def analyze(self, image_path: str, features: list[str] | None = None, prompt: str = "Describe this image in detail.") -> dict[str, Any]:
        """Analyze an image using the configured provider."""
        if self.provider == "openai":
            return await self._openai_analyze(image_path, prompt)
        elif self.provider == "google":
            return await self._google_analyze(image_path, features or ["LABEL_DETECTION", "TEXT_DETECTION", "OBJECT_LOCALIZATION"])
        elif self.provider == "aws":
            return await self._aws_analyze(image_path, features or ["labels", "text"])
        raise ValueError(f"Unsupported vision provider: {self.provider}")

    async def detect_labels(self, image_path: str, max_results: int = 20) -> list[dict[str, Any]]:
        """Detect labels/tags in an image."""
        if self.provider == "openai":
            result = await self._openai_analyze(image_path, "List all objects and elements visible in this image as a JSON array of labels with confidence scores.")
            return [{"label": result.get("description", ""), "confidence": 1.0}]
        elif self.provider == "google":
            result = await self._google_analyze(image_path, ["LABEL_DETECTION"])
            return [{"label": a.get("description", ""), "confidence": a.get("score", 0)} for a in result.get("labelAnnotations", [])][:max_results]
        elif self.provider == "aws":
            result = await self._aws_analyze(image_path, ["labels"])
            return [{"label": l.get("Name", ""), "confidence": l.get("Confidence", 0) / 100} for l in result.get("Labels", [])][:max_results]
        return []

    async def extract_text(self, image_path: str) -> list[dict[str, Any]]:
        """Extract text (OCR) from an image."""
        if self.provider == "openai":
            result = await self._openai_analyze(image_path, "Extract all visible text from this image. Return only the text content.")
            return [{"text": result.get("description", ""), "confidence": 1.0}]
        elif self.provider == "google":
            result = await self._google_analyze(image_path, ["TEXT_DETECTION"])
            return [{"text": a.get("description", ""), "confidence": 1.0} for a in result.get("textAnnotations", [])]
        elif self.provider == "aws":
            result = await self._aws_analyze(image_path, ["text"])
            return [{"text": t.get("DetectedText", ""), "confidence": t.get("Confidence", 0) / 100, "type": t.get("Type", "")} for t in result.get("TextDetections", [])]
        return []

    async def detect_objects(self, image_path: str) -> list[dict[str, Any]]:
        """Detect objects with bounding boxes."""
        if self.provider == "google":
            result = await self._google_analyze(image_path, ["OBJECT_LOCALIZATION"])
            return [{"name": o.get("name", ""), "confidence": o.get("score", 0), "bounding_box": o.get("boundingPoly", {})} for o in result.get("localizedObjectAnnotations", [])]
        elif self.provider == "aws":
            result = await self._aws_analyze(image_path, ["labels"])
            return [{"name": l.get("Name", ""), "confidence": l.get("Confidence", 0) / 100, "instances": l.get("Instances", [])} for l in result.get("Labels", []) if l.get("Instances")]
        return []

    async def classify(self, image_path: str, categories: list[str]) -> dict[str, Any]:
        """Classify image against custom categories (OpenAI only)."""
        cats = ", ".join(categories)
        result = await self._openai_analyze(image_path, f"Classify this image into one of these categories: {cats}. Return a JSON object with category names as keys and confidence scores (0-1) as values.")
        return result

    # ── Provider Implementations ───────────────────────────────

    async def _openai_analyze(self, image_path: str, prompt: str) -> dict[str, Any]:
        b64 = self._encode_image(image_path)
        mime = self._image_mime_type(image_path)
        resp = await self._client.post("/chat/completions", json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
            ]}],
            "max_tokens": 1000,
        })
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return {"description": content, "model": "gpt-4o", "provider": "openai"}

    async def _google_analyze(self, image_path: str, features: list[str]) -> dict[str, Any]:
        b64 = self._encode_image(image_path)
        feature_list = [{"type": f, "maxResults": 50} for f in features]
        resp = await self._client.post(f"/images:annotate?key={self.api_key}", json={
            "requests": [{"image": {"content": b64}, "features": feature_list}]
        })
        resp.raise_for_status()
        responses = resp.json().get("responses", [{}])
        return responses[0] if responses else {}

    async def _aws_analyze(self, image_path: str, features: list[str]) -> dict[str, Any]:
        image_bytes = Path(image_path).read_bytes()
        b64 = base64.b64encode(image_bytes).decode()
        results: dict[str, Any] = {}
        if "labels" in features:
            resp = await self._client.post("/", headers={
                "Content-Type": "application/x-amz-json-1.1",
                "X-Amz-Target": "RekognitionService.DetectLabels",
            }, json={"Image": {"Bytes": b64}, "MaxLabels": 50})
            resp.raise_for_status()
            results.update(resp.json())
        if "text" in features:
            resp = await self._client.post("/", headers={
                "Content-Type": "application/x-amz-json-1.1",
                "X-Amz-Target": "RekognitionService.DetectText",
            }, json={"Image": {"Bytes": b64}})
            resp.raise_for_status()
            results.update(resp.json())
        return results
