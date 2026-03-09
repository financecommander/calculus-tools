"""
Translation Client — Stub for MVP.

Planned capabilities:
- Text translation (single and batch) via DeepL, Google, etc.
- Language detection
- Supported language listing
- Document translation
"""

from typing import Dict, Any, Optional, List


class TranslationClient:
    """Translation API client (stub — not yet implemented)."""

    def __init__(
        self, provider: str = "deepl", api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key

    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Translation translate not yet implemented")

    async def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Translation translate_batch not yet implemented")

    async def detect_language(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError("Translation detect_language not yet implemented")

    async def list_languages(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Translation list_languages not yet implemented")

    async def translate_document(
        self,
        file_path: str,
        target_lang: str,
        output_path: Optional[str] = None,
    ) -> str:
        raise NotImplementedError("Translation translate_document not yet implemented")
