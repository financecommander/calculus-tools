"""Video generation client — Runway Gen-3, Luma Dream Machine adapters.

Usage::

    client = VideoGenClient(provider="runway", api_key="...")
    result = await client.generate_from_text("a timelapse of flowers blooming")
    status = await client.get_status(result["generation_id"])
    video_bytes = await client.download(result["generation_id"])
    await client.close()
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class VideoGenClient:
    """Async video generation client supporting Runway and Luma."""

    def __init__(self, provider: str = "runway", api_key: str = "") -> None:
        self.provider = provider.lower()
        self.api_key = api_key
        if self.provider == "runway":
            self._client = httpx.AsyncClient(
                base_url="https://api.dev.runwayml.com/v1",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "X-Runway-Version": "2024-11-06"},
                timeout=120.0,
            )
        elif self.provider == "luma":
            self._client = httpx.AsyncClient(
                base_url="https://api.lumalabs.ai/dream-machine/v1",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=120.0,
            )
        else:
            self._client = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def generate_from_text(self, prompt: str, *, duration: int = 5, resolution: str = "1080p", model: str = "") -> dict[str, Any]:
        """Generate video from text prompt."""
        if self.provider == "runway":
            payload: dict[str, Any] = {"promptText": prompt, "model": model or "gen3a_turbo", "duration": min(duration, 10), "ratio": "16:9" if resolution == "1080p" else "1:1"}
            resp = await self._client.post("/image_to_video", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Started Runway video generation: %s", data.get("id", ""))
            return {"generation_id": data.get("id", ""), "status": "processing", "provider": "runway"}
        elif self.provider == "luma":
            payload = {"prompt": prompt, "loop": False, "aspect_ratio": "16:9"}
            resp = await self._client.post("/generations", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info("Started Luma video generation: %s", data.get("id", ""))
            return {"generation_id": data.get("id", ""), "status": data.get("state", "queued"), "provider": "luma"}
        return {}

    async def generate_from_image(self, image_path: str, prompt: str, *, duration: int = 5, model: str = "") -> dict[str, Any]:
        """Generate video from image + text prompt."""
        import base64
        image_bytes = Path(image_path).read_bytes()
        b64 = base64.b64encode(image_bytes).decode()
        mime = "image/png" if image_path.endswith(".png") else "image/jpeg"

        if self.provider == "runway":
            payload: dict[str, Any] = {"promptImage": f"data:{mime};base64,{b64}", "promptText": prompt, "model": model or "gen3a_turbo", "duration": min(duration, 10)}
            resp = await self._client.post("/image_to_video", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {"generation_id": data.get("id", ""), "status": "processing", "provider": "runway"}
        elif self.provider == "luma":
            payload = {"prompt": prompt, "keyframes": {"frame0": {"type": "image", "url": f"data:{mime};base64,{b64}"}}}
            resp = await self._client.post("/generations", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {"generation_id": data.get("id", ""), "status": data.get("state", "queued"), "provider": "luma"}
        return {}

    async def generate_avatar(self, script: str, *, avatar_id: str | None = None, voice_id: str | None = None) -> dict[str, Any]:
        """Generate an AI avatar video with script (requires avatar provider like HeyGen)."""
        # Avatar generation typically uses dedicated providers like HeyGen
        import httpx as httpx_
        async with httpx_.AsyncClient(base_url="https://api.heygen.com/v2", headers={"X-Api-Key": self.api_key}, timeout=120.0) as client:
            payload: dict[str, Any] = {
                "video_inputs": [{
                    "character": {"type": "avatar", "avatar_id": avatar_id or "default"},
                    "voice": {"type": "text", "input_text": script, "voice_id": voice_id or "default"},
                }],
                "dimension": {"width": 1920, "height": 1080},
            }
            resp = await client.post("/video/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return {"generation_id": data.get("data", {}).get("video_id", ""), "status": "processing", "provider": "heygen"}

    async def get_status(self, generation_id: str) -> dict[str, Any]:
        """Check generation status."""
        if self.provider == "runway":
            resp = await self._client.get(f"/tasks/{generation_id}")
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "unknown")
            result: dict[str, Any] = {"generation_id": generation_id, "status": status, "progress": data.get("progress", 0)}
            if status == "SUCCEEDED":
                result["output_url"] = data.get("output", [None])[0]
            elif status == "FAILED":
                result["error"] = data.get("failure", "Unknown error")
            return result
        elif self.provider == "luma":
            resp = await self._client.get(f"/generations/{generation_id}")
            resp.raise_for_status()
            data = resp.json()
            state = data.get("state", "unknown")
            result = {"generation_id": generation_id, "status": state}
            if state == "completed":
                assets = data.get("assets", {})
                result["output_url"] = assets.get("video", "")
            elif state == "failed":
                result["error"] = data.get("failure_reason", "Unknown error")
            return result
        return {"generation_id": generation_id, "status": "unknown"}

    async def download(self, generation_id: str, output_path: str = "") -> bytes:
        """Download a completed video."""
        status = await self.get_status(generation_id)
        url = status.get("output_url", "")
        if not url:
            raise ValueError(f"Video not ready or no URL. Status: {status.get('status')}")
        async with httpx.AsyncClient(timeout=120.0) as dl:
            resp = await dl.get(url)
            resp.raise_for_status()
            video_bytes = resp.content
        if output_path:
            Path(output_path).write_bytes(video_bytes)
            logger.info("Downloaded video to %s (%d bytes)", output_path, len(video_bytes))
        return video_bytes

    async def wait_for_completion(self, generation_id: str, timeout: int = 300, poll_interval: int = 5) -> dict[str, Any]:
        """Poll until generation completes or times out."""
        import asyncio
        start = time.time()
        while time.time() - start < timeout:
            status = await self.get_status(generation_id)
            state = status.get("status", "").lower()
            if state in ("succeeded", "completed"):
                return status
            if state in ("failed", "error"):
                raise RuntimeError(f"Video generation failed: {status.get('error', 'Unknown')}")
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Video generation timed out after {timeout}s")
