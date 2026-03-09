"""
Transcription Client — Stub for MVP.

Planned capabilities:
- Audio-to-text transcription (Whisper, etc.)
- URL-based audio transcription
- Transcript summarization
- Speaker diarization (speaker detection)
- Structured meeting notes generation
"""

from typing import Dict, Any, Optional, List


class TranscriptionClient:
    """Transcription API client (stub — not yet implemented)."""

    def __init__(
        self, provider: str = "whisper", api_key: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key

    async def transcribe(
        self, audio_path: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Transcription transcribe not yet implemented")

    async def transcribe_url(
        self, url: str, language: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Transcription transcribe_url not yet implemented")

    async def summarize_transcript(
        self, transcript_text: str, style: str = "bullets"
    ) -> Dict[str, Any]:
        raise NotImplementedError("Transcription summarize_transcript not yet implemented")

    async def detect_speakers(
        self, audio_path: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Transcription detect_speakers not yet implemented")

    async def get_meeting_notes(
        self, audio_path: str, format: str = "structured"
    ) -> Dict[str, Any]:
        raise NotImplementedError("Transcription get_meeting_notes not yet implemented")
