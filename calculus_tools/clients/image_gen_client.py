"""
Image Generation Client — Stub for MVP.

Planned capabilities:
- Text-to-image generation (OpenAI DALL-E, Stability AI, etc.)
- Image editing with masks
- Image variations
- Upscaling
"""

from typing import Dict, Any, Optional, List


class ImageGenClient:
    """Image generation API client (stub — not yet implemented)."""

    def __init__(
        self, provider: str = "openai", api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: Optional[str] = None,
        n: int = 1,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("ImageGen generate not yet implemented")

    async def edit(
        self,
        image_path: str,
        mask_path: str,
        prompt: str,
        size: str = "1024x1024",
    ) -> Dict[str, Any]:
        raise NotImplementedError("ImageGen edit not yet implemented")

    async def variations(
        self, image_path: str, n: int = 1, size: str = "1024x1024"
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("ImageGen variations not yet implemented")

    async def upscale(self, image_path: str, scale: int = 2) -> bytes:
        raise NotImplementedError("ImageGen upscale not yet implemented")
