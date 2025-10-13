from __future__ import annotations

import base64
import io
import os
from typing import Dict

import numpy as np
import soundfile
from fastapi import FastAPI, HTTPException

try:  # pragma: no cover - requires GPU runtime
    from piper import PiperVoice
    from piper.voice import load_voice
except Exception:  # pragma: no cover - fallback path for tests
    PiperVoice = None
    load_voice = None

app = FastAPI(title="FamilyAI Piper Service", version="0.1.0")

_voice: PiperVoice | None = None


def get_voice() -> PiperVoice | None:
    global _voice
    if _voice is not None:
        return _voice
    if PiperVoice is None or load_voice is None:
        return None
    voice_path = os.getenv("VOICE_MODEL", "/voices/en_US-amy-low.onnx")
    config_path = os.getenv("VOICE_CONFIG", "/voices/en_US-amy-low.onnx.json")
    if not os.path.exists(voice_path) or not os.path.exists(config_path):
        return None
    _voice = load_voice(voice_path, config_path)
    return _voice


def synthesize_with_fallback(text: str) -> bytes:
    voice = get_voice()
    if voice is not None:
        audio = voice.synthesize(text)
        return audio
    # Fallback: generate simple sine wave stub so downstream systems keep working
    duration = max(1.0, min(len(text) / 12.0, 5.0))
    sample_rate = 22050
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = 0.1 * np.sin(2 * np.pi * 220 * t)
    buffer = io.BytesIO()
    soundfile.write(buffer, tone, sample_rate, format="WAV")
    return buffer.getvalue()


@app.get("/health", tags=["health"])
def health() -> Dict[str, str]:
    status = "ok" if get_voice() is not None else "degraded"
    return {"status": status}


@app.post("/v1/speak", tags=["tts"])
def speak(request: Dict[str, str]) -> Dict[str, str]:
    text = request.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")
    audio_bytes = synthesize_with_fallback(text)
    payload = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_base64": payload, "mime_type": "audio/wav"}
