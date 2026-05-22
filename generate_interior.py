#!/usr/bin/env python3
"""
Interior Image Generator using Google Gemini API.
Generates interior design images from natural language descriptions.
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash-preview-image-generation"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
OUTPUT_DIR = Path("output")

INTERIOR_STYLES = [
    "Scandinavian minimalist",
    "modern industrial",
    "bohemian eclectic",
    "mid-century modern",
    "coastal",
    "japandi",
    "contemporary luxury",
    "rustic farmhouse",
]

ASPECT_RATIOS = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
    "wide": "4:3",
}


def build_interior_prompt(
    description: str,
    style: str | None = None,
    room_type: str | None = None,
    lighting: str = "natural daylight",
    camera_angle: str = "eye-level perspective",
) -> str:
    """
    Constructs a detailed 5-component prompt optimised for interior images.
    Components: Subject + Action + Location/Context + Composition + Style
    """
    subject = room_type or "interior room"
    if description:
        subject = f"{subject} — {description}"

    style_str = style or "modern contemporary"
    context = f"{style_str} interior design, {lighting}"
    composition = f"{camera_angle}, architectural photography"
    visual_style = (
        "photorealistic, 8K resolution, professionally lit, "
        "sharp focus, editorial interior photography, "
        "clean lines, thoughtful decor"
    )

    prompt = (
        f"A beautifully designed {subject}. "
        f"Setting: {context}. "
        f"Shot with {composition}. "
        f"Style: {visual_style}."
    )
    return prompt


def generate_image(prompt: str, api_key: str) -> bytes | None:
    """Calls Gemini API and returns raw image bytes, or None on failure."""
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }

    response = requests.post(
        f"{API_URL}?key={api_key}",
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        print(f"  [error] API returned {response.status_code}: {response.text[:300]}")
        return None

    data = response.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
    except (KeyError, IndexError):
        print(f"  [error] Unexpected response structure: {json.dumps(data)[:300]}")

    return None


def save_image(image_bytes: bytes, filename: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_bytes(image_bytes)
    return path


def run(args: argparse.Namespace, api_key: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    total = args.batch
    succeeded = 0

    print(f"\nGenerating {total} interior image(s) for: \"{args.description}\"")
    print(f"Style: {args.style or 'auto'} | Room: {args.room or 'auto'} | Lighting: {args.lighting}\n")

    for i in range(1, total + 1):
        # Rotate styles across batch variations
        style = args.style
        if not style and total > 1:
            style = INTERIOR_STYLES[(i - 1) % len(INTERIOR_STYLES)]

        prompt = build_interior_prompt(
            description=args.description,
            style=style,
            room_type=args.room,
            lighting=args.lighting,
            camera_angle=args.angle,
        )

        print(f"[{i}/{total}] Prompt: {prompt[:120]}...")
        image_bytes = generate_image(prompt, api_key)

        if image_bytes:
            filename = f"interior_{timestamp}_{i:02d}.png"
            path = save_image(image_bytes, filename)
            print(f"[{i}/{total}] Saved → {path}\n")
            succeeded += 1
        else:
            print(f"[{i}/{total}] Failed — skipping\n")

    print(f"Done. {succeeded}/{total} image(s) saved to ./{OUTPUT_DIR}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate interior design images using Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_interior.py "open-plan living room with large windows"
  python3 generate_interior.py "cozy reading nook" --style "japandi" --room "study"
  python3 generate_interior.py "master bedroom" --batch 3 --lighting "warm evening light"
  python3 generate_interior.py "kitchen" --batch 4 --angle "wide-angle overhead shot"
        """,
    )
    parser.add_argument("description", help="Natural language description of the interior")
    parser.add_argument("--style", help=f"Design style. Options: {', '.join(INTERIOR_STYLES)}")
    parser.add_argument("--room", help="Room type (e.g. living room, bedroom, kitchen)")
    parser.add_argument("--lighting", default="natural daylight", help="Lighting condition (default: natural daylight)")
    parser.add_argument("--angle", default="eye-level perspective", help="Camera angle (default: eye-level perspective)")
    parser.add_argument("--batch", type=int, default=1, metavar="N", help="Number of variations to generate (default: 1)")

    args = parser.parse_args()

    api_key = GEMINI_API_KEY
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Add it to a .env file or export it in your shell.")
        sys.exit(1)

    if args.batch < 1 or args.batch > 10:
        print("Error: --batch must be between 1 and 10.")
        sys.exit(1)

    run(args, api_key)


if __name__ == "__main__":
    main()
