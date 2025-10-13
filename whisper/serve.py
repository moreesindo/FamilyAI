from __future__ import annotations

import io
import os
from typing import Dict

import soundfile
import torch
import whisper
from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="FamilyAI Whisper Service", version="0.1.0")

_model = None


def get_model() -> whisper.Whisper:
    global _model
    if _model is None:
        model_name = os.getenv("MODEL_NAME", "small")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = whisper.load_model(model_name, device=device)
    return _model


@app.get("/health", tags=["health"])
def health() -> Dict[str, str]:
    get_model()
    return {"status": "ok"}


@app.post("/v1/transcribe", tags=["asr"])
async def transcribe(file: UploadFile = File(...)) -> Dict[str, str]:
    audio_bytes = await file.read()
    audio_buffer = io.BytesIO(audio_bytes)
    audio, _ = soundfile.read(audio_buffer)
    model = get_model()
    result = model.transcribe(audio, fp16=torch.cuda.is_available(), language="en")
    return {"text": result["text"], "language": result.get("language", "en"), "segments": str(result.get("segments", []))}
