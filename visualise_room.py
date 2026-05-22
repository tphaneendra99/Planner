#!/usr/bin/env python3
"""One-shot luxury bedroom visualisation for the SPEKW laminate room."""

import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
IMAGEN_MODEL = "imagen-4.0-generate-001"
BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OUTPUT_DIR = Path("output")

PROMPTS = [
    # Variation 1 – warm greige accent wall, full bed setup
    (
        "A photorealistic luxury master bedroom interior design render. "
        "The room has white Italian marble tile flooring, a false ceiling with recessed LED cove lighting running along the perimeter. "
        "Floor-to-ceiling wardrobe on the left wall with cabinet doors finished in SPEKW RUA-123 beige cream brushed silk laminate — smooth, pearlescent, warm ivory tone. "
        "Accent drawer fronts and vertical panel strips on the wardrobe finished in SPEKW RUA-120 slate blue brushed silk laminate — deep steel blue, cool metallic sheen. "
        "Open shelving unit on the right wall finished in the same beige cream laminate with blue laminate back panels. "
        "Wall colour: warm greige (Benjamin Moore Revere Pewter tone) on three walls, with a deep slate blue (matching RUA-120) feature wall behind the bed headboard. "
        "King-size upholstered bed with cream velvet headboard, layered linen bedding in ivory and dusty blue. "
        "Gold brushed brass bedside pendant lights hanging from ceiling. "
        "Plush cream area rug. Subtle ambient lighting. "
        "Shot with eye-level perspective, wide-angle architectural photography, 8K photorealistic render, luxury interior design magazine quality."
    ),
    # Variation 2 – dark moody walls, dramatic lighting
    (
        "A photorealistic luxury master bedroom 3D visualisation. "
        "White marble floor tiles, false ceiling with warm LED strip cove lighting. "
        "Full-height fitted wardrobe on the back-left wall, doors panelled in SPEKW RUA-123 cream beige brushed silk laminate with gold satin handles. "
        "Accent vertical fluting strips in SPEKW RUA-120 deep slate blue brushed laminate on the wardrobe centre panel and shelving unit back wall. "
        "Wall colour: charcoal off-black (Farrow & Ball Railings tone) on three walls creating a moody, dramatic atmosphere. "
        "Accent wall behind bed: midnight blue with subtle grasscloth texture wallpaper. "
        "King bed with tufted dark navy velvet headboard, silk throw in champagne gold. "
        "Integrated LED wardrobe interior lighting visible through ajar doors. "
        "Two cylindrical brushed gold bedside table lamps. White sheer curtains floor-to-ceiling on window wall. "
        "Luxury hotel bedroom aesthetic, dramatic shadows, warm accent lighting, 8K photorealistic architectural render."
    ),
    # Variation 3 – soft warm whites, Japandi luxury
    (
        "A photorealistic luxury Japandi-style master bedroom render. "
        "Polished white marble flooring, clean false ceiling with hairline LED cove lighting. "
        "Floor-to-ceiling wardrobe left wall with push-to-open handleless doors in SPEKW RUA-123 warm cream beige brushed silk laminate. "
        "Thin vertical accent strips and bottom plinth in SPEKW RUA-120 slate blue brushed silk laminate. "
        "Open shelving unit right wall: cream laminate shelves, slate blue back panel, displaying minimal ceramic vases and books. "
        "Wall colour: warm white (almost off-white, Swiss Coffee tone) on all walls. "
        "Low-profile platform king bed in natural oak with cream boucle headboard, white linen bedding with dusty blue throw. "
        "Wabi-sabi ceramic table lamps in matte beige. Large monstera plant in terracotta pot in corner. "
        "Soft diffused morning light from sheer white curtains. "
        "Serene, uncluttered, editorial interior photography, 8K photorealistic, luxury minimalist aesthetic."
    ),
]


def generate_imagen(prompt: str, index: int) -> bool:
    """Use Imagen 4.0 via the predict endpoint — best quality."""
    url = f"{BASE}/{IMAGEN_MODEL}:predict?key={API_KEY}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"},
    }
    resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=120)
    if resp.status_code != 200:
        print(f"      [imagen error] {resp.status_code}: {resp.text[:300]}")
        return False
    data = resp.json()
    try:
        b64 = data["predictions"][0]["bytesBase64Encoded"]
    except (KeyError, IndexError):
        print(f"      [imagen error] Unexpected response: {json.dumps(data)[:300]}")
        return False
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"luxury_bedroom_v{index}.png"
    path.write_bytes(base64.b64decode(b64))
    print(f"      Saved → {path}")
    return True


def generate_gemini(prompt: str, index: int) -> bool:
    """Fallback: Gemini 3.1 Flash Image via generateContent."""
    url = f"{BASE}/{GEMINI_IMAGE_MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=120)
    if resp.status_code != 200:
        print(f"      [gemini error] {resp.status_code}: {resp.text[:300]}")
        return False
    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        print(f"      [gemini error] Unexpected response: {json.dumps(data)[:300]}")
        return False
    for part in parts:
        if "inlineData" in part:
            OUTPUT_DIR.mkdir(exist_ok=True)
            path = OUTPUT_DIR / f"luxury_bedroom_v{index}.png"
            path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
            print(f"      Saved → {path}")
            return True
        if "text" in part and part["text"].strip():
            print(f"      Model note: {part['text'].strip()[:200]}")
    return False


def generate(prompt: str, index: int) -> None:
    print(f"\n[{index}/3] Generating variation {index}...")
    print(f"      {prompt[:100]}...")
    print("      Trying Imagen 4.0...")
    if not generate_imagen(prompt, index):
        print("      Falling back to Gemini 3.1 Flash Image...")
        generate_gemini(prompt, index)


if __name__ == "__main__":
    if not API_KEY:
        print("GEMINI_API_KEY not set.")
        sys.exit(1)

    print("=" * 60)
    print("Luxury Bedroom Visualiser — SPEKW RUA-123 + RUA-120")
    print("Generating 3 variations...")
    print("=" * 60)

    for i, prompt in enumerate(PROMPTS, 1):
        generate(prompt, i)

    print("\nAll done. Check ./output/ for your renders.")
