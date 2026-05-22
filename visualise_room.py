#!/usr/bin/env python3
"""
Luxury bedroom visualiser — sends the actual room photo to Gemini
as a multimodal reference so the output matches the real room layout.
"""

import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.1-flash-image-preview"
BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OUTPUT_DIR = Path("output")

# ── Precise description of the actual room observed in the photo ──────────────
ROOM_CONTEXT = """
The reference room is a bedroom under construction with these exact features:
- Large-format white marble tile flooring with subtle grey veining
- White gypsum false ceiling with warm LED strip cove lighting running along all four perimeter edges
- Back wall: full-width floor-to-ceiling built-in wardrobe/cabinet unit —
    upper section has overhead loft storage cabinets spanning full wall width,
    main section has two tall wardrobe door panels on the left,
    a central recessed TV/display unit with open niches,
    and a light-coloured back panel in the centre niche
- Right side: a separate freestanding open-shelf bookcase unit (5-6 shelves, rectangular)
- Left wall: a dark wood-framed entry door leading to another room
- Room is medium-sized (approx 12×12 ft), currently bare — no furniture, no bed yet
"""

VARIATIONS = [
    {
        "name": "warm_greige",
        "wall": "warm greige (similar to Duluxালtape or Benjamin Moore Revere Pewter) on three walls, with a deep slate blue feature wall directly behind where the bed headboard will sit",
        "mood": "classic warm luxury",
        "furniture": (
            "king-size bed with cream velvet upholstered headboard, ivory linen bedding with dusty blue throw, "
            "two brushed gold pendant bedside lights hanging from ceiling, a plush cream area rug, "
            "a sleek low oak sideboard with gold handles under the TV niche"
        ),
    },
    {
        "name": "dark_dramatic",
        "wall": "deep charcoal (near black, similar to Farrow & Ball Railings) on three walls, midnight navy blue textured wallpaper on the feature wall behind the bed",
        "mood": "dark dramatic luxury hotel",
        "furniture": (
            "king-size bed with deep navy blue tufted velvet headboard, champagne gold silk throw, "
            "integrated LED strip lighting inside the wardrobe visible through slightly open doors, "
            "two cylindrical brushed gold table lamps on floating bedside shelves, "
            "white sheer floor-to-ceiling curtains on one side"
        ),
    },
    {
        "name": "japandi_minimal",
        "wall": "warm off-white (Swiss Coffee tone) on all four walls, keeping it light and serene",
        "mood": "Japandi minimalist luxury",
        "furniture": (
            "low-profile platform king bed in natural oak with cream boucle headboard, "
            "crisp white linen bedding with a single dusty blue linen throw, "
            "two wabi-sabi matte beige ceramic table lamps, "
            "a large monstera plant in a terracotta pot in the corner, "
            "a thin natural jute rug under the bed"
        ),
    },
]


def build_prompt(v: dict) -> str:
    return f"""
You are an expert interior designer and photorealistic 3D visualisation artist.

TASK: Transform the reference room described below into a fully finished luxury master bedroom.
Generate a single photorealistic image showing the completed room.

REFERENCE ROOM LAYOUT:
{ROOM_CONTEXT}

LAMINATE FINISHES TO APPLY:
- Wardrobe door panels, overhead loft cabinet doors, and shelving unit shelves:
  SPEKW RUA-123 — warm beige / pearl cream brushed silk laminate finish
  (smooth, soft sheen, warm ivory tone, subtle brush texture)
- Accent elements — centre vertical strip on wardrobe, drawer fronts, back panel of TV niche,
  and back panels of the bookshelf unit:
  SPEKW RUA-120 — deep slate blue brushed silk laminate
  (cool steel blue, subtle metallic brushed sheen)
- All handles / hardware: brushed satin gold / brass

WALL COLOUR: {v["wall"]}

FURNITURE & ACCESSORIES TO ADD:
{v["furniture"]}

DESIGN MOOD: {v["mood"]}

OUTPUT REQUIREMENTS:
- Photorealistic render, 4K quality, sharp focus
- Eye-level perspective showing the full wardrobe wall and bed
- Warm ambient lighting from the existing LED cove ceiling lights plus new bedside lamps
- The white marble floor must remain visible
- The false ceiling with LED cove lighting must remain as-is
- Interior design magazine editorial quality
- Do NOT change the room structure — keep the same wardrobe layout, shelf unit, door position
""".strip()


def generate(prompt: str, name: str, index: int) -> None:
    print(f"\n[{index}/3] Generating: {name}...")

    url = f"{BASE}/{MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    if resp.status_code != 200:
        print(f"  [error] {resp.status_code}: {resp.text[:400]}")
        return

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError):
        print(f"  [error] Unexpected response: {json.dumps(data)[:300]}")
        return

    saved = False
    for part in parts:
        if "inlineData" in part:
            OUTPUT_DIR.mkdir(exist_ok=True)
            path = OUTPUT_DIR / f"bedroom_{name}_v{index}.png"
            path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
            print(f"  Saved → {path}")
            saved = True
        elif "text" in part and part["text"].strip():
            print(f"  Note: {part['text'].strip()[:200]}")

    if not saved:
        # fallback to Imagen 4.0
        print("  Gemini returned no image — trying Imagen 4.0...")
        generate_imagen(prompt, name, index)


def generate_imagen(prompt: str, name: str, index: int) -> None:
    url = f"{BASE}/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"},
    }
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code != 200:
        print(f"  [imagen error] {resp.status_code}: {resp.text[:300]}")
        return
    data = resp.json()
    try:
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR / f"bedroom_{name}_v{index}.png"
        path.write_bytes(base64.b64decode(b64))
        print(f"  Saved → {path}")
    except (KeyError, IndexError):
        print(f"  [imagen error] Unexpected: {json.dumps(data)[:300]}")


if __name__ == "__main__":
    if not API_KEY:
        print("GEMINI_API_KEY not set.")
        sys.exit(1)

    print("=" * 60)
    print("Luxury Bedroom Visualiser — Your Actual Room")
    print("SPEKW RUA-123 (cream) + RUA-120 (slate blue)")
    print("=" * 60)

    for i, v in enumerate(VARIATIONS, 1):
        generate(build_prompt(v), v["name"], i)

    print("\nDone. Images saved to ./output/")
