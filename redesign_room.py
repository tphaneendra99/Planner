#!/usr/bin/env python3
"""
Room redesign using Imagen 4.0 Ultra — based on exact visual observation
of the uploaded room photo and SPEKW laminate samples.
"""

import base64, json, os, sys
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("GEMINI_API_KEY")
BASE     = "https://generativelanguage.googleapis.com/v1beta/models"
OUT      = Path("output")

# ── Exact laminate colours observed from the sample photos ───────────────────
# RUA-123: brushed silver-cream / warm pearl white, subtle horizontal brush strokes, silky sheen
# RUA-120: brushed dark slate grey, cool charcoal with slight blue undertone, metallic silk finish

BASE_PROMPT = """
Photorealistic 3D interior design render of a bedroom.

EXACT ROOM STRUCTURE (do not change any of this):
- Camera angle: wide-angle view from the front-left corner of the room, looking diagonally toward the back-right wall
- Floor: large-format white marble tiles, bright white with faint grey veining, highly reflective
- Ceiling: flat white gypsum false ceiling with LED strip cove lighting glowing warm white along all four perimeter edges; a ceiling fan mounting point at centre
- Back wall (main feature): full-width floor-to-ceiling built-in wardrobe unit:
    • Top strip: full-width overhead loft storage cabinets about 2 feet tall, flush against the ceiling
    • Main wardrobe left section: three tall vertical shutter doors side by side, approx 6 feet tall
    • Main wardrobe right section: an open-niche TV/display unit with a recessed cubby and a flat back panel
- Right side: a large freestanding open bookshelf unit, approximately 5 feet wide and 7 feet tall with 5 shelves, standing against the right wall
- Left wall: a door with dark brown wood frame, painted white panel door, leading to a hallway; electrical switch plates on the wall beside it

LAMINATE FINISH TO APPLY ON ALL CABINET/WARDROBE SURFACES:
- All wardrobe shutter door faces, overhead loft cabinet door faces, and bookshelf shelf faces:
  SPEKW RUA-123 finish — brushed pearl-white / warm silver-cream laminate,
  silky smooth surface with subtle horizontal brush-stroke texture, soft luminous sheen,
  warm ivory-white tone (NOT stark white, slightly warm like cream)
- Accent elements — the flat back panel inside the TV niche, thin vertical groove lines between wardrobe doors, and bookshelf back panels:
  SPEKW RUA-120 finish — brushed dark slate grey laminate,
  cool charcoal grey with a slight steel-blue undertone, metallic silk finish
- All handles and hardware: matte brushed gold / satin brass

{wall_and_furnishing}

RENDER QUALITY:
- 4K photorealistic architectural visualisation
- Warm ambient glow from ceiling LED cove lights
- Sharp focus throughout, no motion blur
- Interior design magazine quality, like a Architectural Digest spread
- The room must feel complete and luxury — no construction materials, no debris
"""

VARIATIONS = [
    {
        "file": "redesign_warm_v1.png",
        "label": "Warm Greige + Gold",
        "wall_and_furnishing": """
WALL COLOUR: warm greige (similar to Dulux Pebble Shore) on the left wall and ceiling;
the back wall behind the wardrobe is not visible;
the right wall (behind the bookshelf) in same warm greige.
No feature/accent wall — keep it subtle and warm.

FURNISHING: king-size bed positioned in front of the wardrobe (centre of room),
low-profile platform bed in natural light oak wood,
cream bouclé fabric upholstered headboard (no footboard),
white linen bedding layered with a dusty blue linen throw and cream cushions,
two brushed brass/gold cylindrical pendant lights hanging from ceiling on either side of bed,
a thin natural jute rug under the bed,
small white ceramic vases on bookshelf,
soft warm ambient lighting overall.
"""
    },
    {
        "file": "redesign_dark_v2.png",
        "label": "Dark Charcoal + Drama",
        "wall_and_furnishing": """
WALL COLOUR: deep charcoal (Farrow & Ball Railings, near-black with warm undertone)
on the left and right visible walls.
This creates dramatic contrast against the cream laminate wardrobes.

FURNISHING: king-size bed in centre of room facing the wardrobe,
dark slate upholstered bed frame with a tall tufted navy velvet headboard,
charcoal grey linen bedding with a single champagne gold silk throw,
integrated warm LED strip lighting inside wardrobe niches visible through partially open doors,
two brushed gold arc floor lamps flanking the bed,
dark grey plush area rug under the bed,
gold-framed abstract wall art above the bookshelf.
"""
    },
    {
        "file": "redesign_japandi_v3.png",
        "label": "Japandi Off-White",
        "wall_and_furnishing": """
WALL COLOUR: warm off-white / Swiss Coffee on all visible walls — clean, serene, uncluttered.

FURNISHING: very low floor-level platform king bed in solid dark walnut wood,
simple cream boucle headboard, crisp white linen bedding, single grey cotton throw,
minimalist brushed brass table lamp on a low oak bedside table,
a large terracotta pot with a monstera plant in the far right corner,
a thin cream shaggy rug under the bed,
books and minimal ceramic objects on the bookshelf,
serene morning light mood, shadows soft and diffused.
"""
    },
]


def call_imagen_ultra(prompt: str, filename: str, label: str, idx: int) -> bool:
    print(f"\n[{idx}/3] {label}")
    url = f"{BASE}/imagen-4.0-ultra-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"},
    }
    r = requests.post(url, headers={"Content-Type": "application/json"},
                      json=payload, timeout=180)
    if r.status_code != 200:
        print(f"  [ultra error] {r.status_code}: {r.text[:300]}")
        return False
    data = r.json()
    try:
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        OUT.mkdir(exist_ok=True)
        path = OUT / filename
        path.write_bytes(base64.b64decode(b64))
        print(f"  Saved → {path}")
        return True
    except (KeyError, IndexError):
        print(f"  [ultra error] Response: {json.dumps(data)[:300]}")
        return False


def call_imagen_standard(prompt: str, filename: str) -> bool:
    url = f"{BASE}/imagen-4.0-generate-001:predict?key={API_KEY}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"},
    }
    r = requests.post(url, headers={"Content-Type": "application/json"},
                      json=payload, timeout=180)
    if r.status_code != 200:
        print(f"  [std error] {r.status_code}: {r.text[:300]}")
        return False
    data = r.json()
    try:
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        OUT.mkdir(exist_ok=True)
        path = OUT / filename
        path.write_bytes(base64.b64decode(b64))
        print(f"  Saved (std) → {path}")
        return True
    except (KeyError, IndexError):
        print(f"  [std error] Response: {json.dumps(data)[:300]}")
        return False


if __name__ == "__main__":
    if not API_KEY:
        print("GEMINI_API_KEY not set.")
        sys.exit(1)

    print("=" * 60)
    print("Room Redesign — SPEKW RUA-123 (cream) + RUA-120 (slate grey)")
    print("Using Imagen 4.0 Ultra")
    print("=" * 60)

    for i, v in enumerate(VARIATIONS, 1):
        prompt = BASE_PROMPT.format(wall_and_furnishing=v["wall_and_furnishing"]).strip()
        ok = call_imagen_ultra(prompt, v["file"], v["label"], i)
        if not ok:
            print("  Falling back to Imagen 4.0 standard...")
            call_imagen_standard(prompt, v["file"])

    print(f"\nDone. Check ./{OUT}/")
