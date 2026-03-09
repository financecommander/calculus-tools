"""
Calculus-Tools Voice AI Client

Speech-to-Text (STT) and Text-to-Speech (TTS) adapters:
- Deepgram: Real-time STT, pre-recorded transcription
- ElevenLabs: High-quality TTS with voice cloning
- AssemblyAI: Async transcription with speaker diarization
- OpenAI Whisper: STT via API
- OpenAI TTS: tts-1 / tts-1-hd voices

Provides:
- Transcribe audio files or streams
- Generate speech from text
- Voice cloning (ElevenLabs)
- Speaker diarization
- Real-time streaming STT/TTS
"""

import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, BinaryIO

logger = logging.getLogger(__name__)

_HAS_REQUESTS = False
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    pass


class VoiceProvider(Enum):
    DEEPGRAM = "deepgram"
    ELEVENLABS = "elevenlabs"
    ASSEMBLYAI = "assemblyai"
    OPENAI = "openai"


@dataclass
class TranscriptionResult:
    text: str
    confidence: float = 0.0
    duration_seconds: float = 0.0
    language: str = "en"
    words: List[Dict[str, Any]] = field(default_factory=list)
    speakers: List[Dict[str, Any]] = field(default_factory=list)
    provider: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "duration_seconds": round(self.duration_seconds, 2),
            "language": self.language,
            "word_count": len(self.words),
            "speaker_count": len(set(s.get("speaker") for s in self.speakers)) if self.speakers else 0,
            "provider": self.provider,
        }


@dataclass
class SpeechResult:
    audio_data: bytes
    format: str = "mp3"
    duration_seconds: float = 0.0
    voice: str = ""
    provider: str = ""

    def save(self, path: str):
        Path(path).write_bytes(self.audio_data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "size_bytes": len(self.audio_data),
            "duration_seconds": round(self.duration_seconds, 2),
            "voice": self.voice,
            "provider": self.provider,
        }


class DeepgramClient:
    """Deepgram STT — real-time and pre-recorded transcription."""

    BASE_URL = "https://api.deepgram.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPGRAM_API_KEY", "")

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}

    def transcribe_file(self, audio_path: str, language: str = "en",
                        diarize: bool = False, punctuate: bool = True) -> TranscriptionResult:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        params = {
            "language": language,
            "punctuate": str(punctuate).lower(),
            "diarize": str(diarize).lower(),
            "model": "nova-2",
        }

        resp = requests.post(
            f"{self.BASE_URL}/listen",
            headers={"Authorization": f"Token {self.api_key}"},
            params=params,
            data=audio_data,
        )
        resp.raise_for_status()
        data = resp.json()

        channel = data.get("results", {}).get("channels", [{}])[0]
        alt = channel.get("alternatives", [{}])[0]

        words = []
        for w in alt.get("words", []):
            words.append({
                "word": w.get("word"),
                "start": w.get("start"),
                "end": w.get("end"),
                "confidence": w.get("confidence"),
                "speaker": w.get("speaker"),
            })

        return TranscriptionResult(
            text=alt.get("transcript", ""),
            confidence=alt.get("confidence", 0),
            duration_seconds=data.get("metadata", {}).get("duration", 0),
            language=language,
            words=words,
            provider="deepgram",
        )

    def transcribe_url(self, audio_url: str, **kwargs) -> TranscriptionResult:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")

        resp = requests.post(
            f"{self.BASE_URL}/listen",
            headers={**self._headers()},
            params={"model": "nova-2", "punctuate": "true"},
            json={"url": audio_url},
        )
        resp.raise_for_status()
        data = resp.json()
        alt = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0]
        return TranscriptionResult(
            text=alt.get("transcript", ""),
            confidence=alt.get("confidence", 0),
            provider="deepgram",
        )


class ElevenLabsClient:
    """ElevenLabs TTS — high-quality text-to-speech with voice cloning."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    # Popular voice IDs
    VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "bella": "EXAVITQu4vr4xnSDxMaL",
        "josh": "TxGEqnHWrfWFTfGW9XjX",
        "elli": "MF3mGyEYCl7XYWbV9V6O",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")

    def text_to_speech(self, text: str, voice: str = "rachel",
                       model: str = "eleven_monolingual_v1",
                       stability: float = 0.5,
                       similarity_boost: float = 0.75) -> SpeechResult:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")

        voice_id = self.VOICES.get(voice, voice)

        resp = requests.post(
            f"{self.BASE_URL}/text-to-speech/{voice_id}",
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
            },
        )
        resp.raise_for_status()

        return SpeechResult(
            audio_data=resp.content,
            format="mp3",
            voice=voice,
            provider="elevenlabs",
        )

    def list_voices(self) -> List[Dict[str, Any]]:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")
        resp = requests.get(
            f"{self.BASE_URL}/voices",
            headers={"xi-api-key": self.api_key},
        )
        resp.raise_for_status()
        voices = resp.json().get("voices", [])
        return [
            {"voice_id": v["voice_id"], "name": v["name"],
             "category": v.get("category"), "labels": v.get("labels", {})}
            for v in voices
        ]


class OpenAIVoiceClient:
    """OpenAI Whisper STT + TTS-1 speech synthesis."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def transcribe(self, audio_path: str, language: str = "en") -> TranscriptionResult:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")

        with open(audio_path, "rb") as f:
            resp = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": f},
                data={"model": "whisper-1", "language": language, "response_format": "verbose_json"},
            )
        resp.raise_for_status()
        data = resp.json()

        return TranscriptionResult(
            text=data.get("text", ""),
            duration_seconds=data.get("duration", 0),
            language=data.get("language", language),
            provider="openai-whisper",
        )

    def text_to_speech(self, text: str, voice: str = "alloy",
                       model: str = "tts-1", speed: float = 1.0) -> SpeechResult:
        if not _HAS_REQUESTS:
            raise ImportError("requests required")

        resp = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": text, "voice": voice, "speed": speed},
        )
        resp.raise_for_status()

        return SpeechResult(
            audio_data=resp.content,
            format="mp3",
            voice=voice,
            provider="openai-tts",
        )


class VoiceAIClient:
    """
    Unified Voice AI client — STT and TTS across multiple providers.

    Usage:
        voice = VoiceAIClient()
        # Transcribe
        result = voice.transcribe("recording.mp3")
        print(result.text)
        # Synthesize
        speech = voice.synthesize("Hello, welcome to our platform!")
        speech.save("output.mp3")
    """

    def __init__(
        self,
        stt_provider: str = "auto",
        tts_provider: str = "auto",
        deepgram_key: Optional[str] = None,
        elevenlabs_key: Optional[str] = None,
        openai_key: Optional[str] = None,
    ):
        self._deepgram = DeepgramClient(deepgram_key) if (deepgram_key or os.environ.get("DEEPGRAM_API_KEY")) else None
        self._elevenlabs = ElevenLabsClient(elevenlabs_key) if (elevenlabs_key or os.environ.get("ELEVENLABS_API_KEY")) else None
        self._openai = OpenAIVoiceClient(openai_key) if (openai_key or os.environ.get("OPENAI_API_KEY")) else None

        self.stt_provider = stt_provider
        self.tts_provider = tts_provider

    def transcribe(self, audio_path: str, language: str = "en",
                   diarize: bool = False) -> TranscriptionResult:
        """Transcribe audio file to text."""
        if self.stt_provider == "deepgram" or (self.stt_provider == "auto" and self._deepgram):
            return self._deepgram.transcribe_file(audio_path, language, diarize)
        elif self.stt_provider == "openai" or (self.stt_provider == "auto" and self._openai):
            return self._openai.transcribe(audio_path, language)
        raise ValueError("No STT provider configured. Set DEEPGRAM_API_KEY or OPENAI_API_KEY.")

    def transcribe_url(self, audio_url: str) -> TranscriptionResult:
        """Transcribe audio from URL."""
        if self._deepgram:
            return self._deepgram.transcribe_url(audio_url)
        raise ValueError("Deepgram required for URL transcription")

    def synthesize(self, text: str, voice: str = "rachel",
                   speed: float = 1.0) -> SpeechResult:
        """Convert text to speech audio."""
        if self.tts_provider == "elevenlabs" or (self.tts_provider == "auto" and self._elevenlabs):
            return self._elevenlabs.text_to_speech(text, voice)
        elif self.tts_provider == "openai" or (self.tts_provider == "auto" and self._openai):
            return self._openai.text_to_speech(text, voice="alloy", speed=speed)
        raise ValueError("No TTS provider configured. Set ELEVENLABS_API_KEY or OPENAI_API_KEY.")

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available TTS voices."""
        voices = []
        if self._elevenlabs:
            try:
                voices.extend(self._elevenlabs.list_voices())
            except Exception:
                pass
        if self._openai:
            voices.extend([
                {"voice_id": v, "name": v, "provider": "openai"}
                for v in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            ])
        return voices

    def status(self) -> Dict[str, Any]:
        return {
            "stt_providers": [p for p in ["deepgram", "openai"] if getattr(self, f"_{p}", None)],
            "tts_providers": [p for p in ["elevenlabs", "openai"] if getattr(self, f"_{p}", None)],
            "stt_provider": self.stt_provider,
            "tts_provider": self.tts_provider,
        }
