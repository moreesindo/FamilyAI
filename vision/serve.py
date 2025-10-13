from __future__ import annotations

import io
from collections import Counter
from typing import Dict

from fastapi import FastAPI, File, Form, UploadFile
from PIL import Image

app = FastAPI(title="FamilyAI Vision Service", version="0.1.0")


@app.get("/health", tags=["health"])
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/vision", tags=["vision"])
async def describe_image(file: UploadFile = File(...), prompt: str = Form("Describe")) -> Dict[str, str]:
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    width, height = image.size
    pixels = image.getdata()
    counter = Counter(pixels)
    dominant_rgb, _ = counter.most_common(1)[0]
    dominant_hex = "#%02x%02x%02x" % dominant_rgb
    return {
        "prompt": prompt,
        "width": width,
        "height": height,
        "dominant_color": dominant_hex,
        "summary": f"Image {width}x{height} with dominant color {dominant_hex}",
    }
