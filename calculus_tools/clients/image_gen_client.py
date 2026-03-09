"""Image generation client — DALL-E 3, Stability AI adapters.

Usage::

    client = ImageGenClient(provider="openai", api_key="sk-...")
    images = await client.generate("a futuristic city at sunset", size="1024x1024")
    edited = await client.edit("base.png", "mask.png", "add a rainbow")
    await client.close()
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ImageGenClient:
    """Async image generation client supporting OpenAI DALL-E and Stability AI."""

    def __init__(self, provider: str = "openai", api_key: str = "") -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        if self.provider == "openai":
            self._client = httpx.AsyncClient(
                base_url="https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=120.0,
            )
        elif self.provider == "stability":
            self._client = httpx.AsyncClient(
                base_url="https://api.stability.ai/v2beta",
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                timeout=120.0,
            )
        else:
            self._client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def generate(self, prompt: str, *, size: str = "1024x1024", style: str | None = None, n: int = 1, model: str = "", quality: str = "standard") -> list[dict[str, Any]]:
        """Generate images from a text prompt."""
        if self.provider == "openai":
            payload: dict[str, Any] = {"prompt": prompt, "n": n, "size": size, "response_format": "b64_json", "model": model or "dall-e-3", "quality": quality}
            if style:
                payload["style"] = style
            resp = await self._client.post("/images/generations", json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("data", []):
                results.append({"b64_json": item.get("b64_json", ""), "revised_prompt": item.get("revised_prompt", prompt), "url": item.get("url", "")})
            logger.info("Generated %d images via OpenAI DALL-E", len(results))
            return results
        elif self.provider == "stability":
            resp = await self._client.post("/stable-image/generate/core", data={"prompt": prompt, "output_format": "png", "aspect_ratio": self._size_to_aspect(size)}, files={"none": ("", b"")})
            resp.raise_for_status()
            data = resp.json()
            image_b64 = data.get("image", "")
            return [{"b64_json": image_b64, "revised_prompt": prompt, "finish_reason": data.get("finish_reason", "")}]
        return []

    async def edit(self, image_path: str, mask_path: str, prompt: str, *, size: str = "1024x1024", model: str = "") -> dict[str, Any]:
        """Edit an image using a mask (inpainting)."""
        if self.provider == "openai":
            image_bytes = Path(image_path).read_bytes()
            mask_bytes = Path(mask_path).read_bytes()
            resp = await self._client.post("/images/edits", data={"prompt": prompt, "size": size, "model": model or "dall-e-2", "response_format": "b64_json"}, files={"image": ("image.png", image_bytes, "image/png"), "mask": ("mask.png", mask_bytes, "image/png")})
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [{}])[0]
        elif self.provider == "stability":
            image_bytes = Path(image_path).read_bytes()
            mask_bytes = Path(mask_path).read_bytes()
            resp = await self._client.post("/stable-image/edit/inpaint", data={"prompt": prompt, "output_format": "png"}, files={"image": ("image.png", image_bytes, "image/png"), "mask": ("mask.png", mask_bytes, "image/png")})
            resp.raise_for_status()
            return resp.json()
        return {}

    async def variations(self, image_path: str, *, n: int = 1, size: str = "1024x1024") -> list[dict[str, Any]]:
        """Generate variations of an image (OpenAI only)."""
        if self.provider == "openai":
            image_bytes = Path(image_path).read_bytes()
            resp = await self._client.post("/images/variations", data={"n": str(n), "size": size, "response_format": "b64_json"}, files={"image": ("image.png", image_bytes, "image/png")})
            resp.raise_for_status()
            return resp.json().get("data", [])
        return []

    async def upscale(self, image_path: str, *, scale: int = 2) -> bytes:
        """Upscale an image (Stability AI)."""
        if self.provider == "stability":
            image_bytes = Path(image_path).read_bytes()
            resp = await self._client.post("/stable-image/upscale/fast", data={"output_format": "png"}, files={"image": ("image.png", image_bytes, "image/png")})
            resp.raise_for_status()
            data = resp.json()
            return base64.b64decode(data.get("image", ""))
        raise NotImplementedError(f"Upscale not supported for provider: {self.provider}")

    async def save_images(self, results: list[dict[str, Any]], output_dir: str, prefix: str = "gen") -> list[str]:
        """Save generated images to disk. Returns list of file paths."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, img in enumerate(results):
            b64 = img.get("b64_json", "")
            if b64:
                path = out / f"{prefix}_{i}.png"
                path.write_bytes(base64.b64decode(b64))
                paths.append(str(path))
        logger.info("Saved %d images to %s", len(paths), output_dir)
        return paths

    @staticmethod
    def _size_to_aspect(size: str) -> str:
        """Convert size string to aspect ratio for Stability AI."""
        ratios = {"1024x1024": "1:1", "1792x1024": "16:9", "1024x1792": "9:16"}
        return ratios.get(size, "1:1")
