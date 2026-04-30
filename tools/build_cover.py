#!/usr/bin/env python3
"""Build the Kaggle cover image for the hackathon submission.

Composes a 1200x630 cover (Kaggle's preferred aspect for cards) with:
- Left half: dark gradient with title, subtitle, and stats
- Right half: the rendered Knowledge Graph screenshot, with a subtle scrim

Output: cover.png at the repo root.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = Path(__file__).resolve().parents[1]
GRAPH_SCREENSHOT = REPO / "screenshots" / "graph network.png"
LOGO = REPO / "gemm4.png"
OUT = REPO / "cover.png"

W, H = 1200, 630
LEFT_W = 580   # left text panel width
PAD = 50

# Color palette (matches the app theme)
PURPLE_A = (47, 32, 116)     # darker indigo
PURPLE_B = (79, 70, 229)     # primary indigo
ACCENT = (245, 158, 11)      # amber
TEXT = (250, 250, 252)
MUTED = (167, 162, 207)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    candidates_reg = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in (candidates_bold if bold else candidates_reg):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _vertical_gradient(size, top, bot):
    img = Image.new("RGB", size, top)
    px = img.load()
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bot[0] * t)
        g = int(top[1] * (1 - t) + bot[1] * t)
        b = int(top[2] * (1 - t) + bot[2] * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def main() -> None:
    # ── Background — subtle diagonal gradient on the LEFT panel ────────
    canvas = Image.new("RGB", (W, H), (15, 23, 42))

    left = _vertical_gradient((LEFT_W, H), PURPLE_A, PURPLE_B)
    canvas.paste(left, (0, 0))

    # ── Right panel — the Knowledge Graph screenshot, downsampled & scrimmed
    if GRAPH_SCREENSHOT.exists():
        graph = Image.open(GRAPH_SCREENSHOT).convert("RGB")
        right_w = W - LEFT_W
        gr_w, gr_h = graph.size
        scale = max(right_w / gr_w, H / gr_h)
        new_w, new_h = int(gr_w * scale), int(gr_h * scale)
        graph = graph.resize((new_w, new_h), Image.LANCZOS)
        # Center-crop to right panel size
        cx, cy = new_w // 2, new_h // 2
        graph = graph.crop((cx - right_w // 2, cy - H // 2,
                            cx + right_w // 2, cy + H // 2))
        # Soften the right side so it doesn't fight the text
        scrim = Image.new("RGB", graph.size, (15, 23, 42))
        graph = Image.blend(graph, scrim, 0.25)
        canvas.paste(graph, (LEFT_W, 0))

    # ── Soft seam between panels ───────────────────────────────────────
    seam = Image.new("RGB", (40, H), PURPLE_B).filter(ImageFilter.GaussianBlur(20))
    canvas.paste(seam, (LEFT_W - 20, 0))

    draw = ImageDraw.Draw(canvas, "RGBA")

    # ── Logo (top-left) ───────────────────────────────────────────────
    if LOGO.exists():
        logo = Image.open(LOGO).convert("RGBA")
        target_h = 64
        ratio = target_h / logo.height
        logo = logo.resize((int(logo.width * ratio), target_h), Image.LANCZOS)
        canvas.paste(logo, (PAD, PAD), logo)

    # ── Title block ────────────────────────────────────────────────────
    f_kicker = _font(18, bold=True)
    f_title = _font(64, bold=True)
    f_sub = _font(24)
    f_stat_n = _font(36, bold=True)
    f_stat_l = _font(13)

    y = PAD + 90
    draw.text((PAD, y), "GEMMA 4 GOOD HACKATHON",
              font=f_kicker, fill=ACCENT)
    y += 38
    draw.text((PAD, y), "A Tutor for", font=f_title, fill=TEXT)
    y += 70
    draw.text((PAD, y), "Every Course.", font=f_title, fill=TEXT)
    y += 90

    # subtitle
    sub = "Open-source. Offline. Private."
    draw.text((PAD, y), sub, font=f_sub, fill=MUTED)
    y += 36
    draw.text((PAD, y), "Powered by Gemma 4 on a 24 GB laptop.",
              font=f_sub, fill=MUTED)

    # ── Stat strip (bottom-left) ──────────────────────────────────────
    stats = [
        ("254", "wiki pages"),
        ("1,178", "graph edges"),
        ("$0", "per student"),
    ]
    sy = H - 110
    sx = PAD
    for n, label in stats:
        draw.text((sx, sy), n, font=f_stat_n, fill=ACCENT)
        n_w = draw.textbbox((0, 0), n, font=f_stat_n)[2]
        draw.text((sx, sy + 46), label, font=f_stat_l, fill=MUTED)
        sx += max(n_w, 90) + 32

    # ── Footer line ───────────────────────────────────────────────────
    f_url = _font(15)
    draw.text((PAD, H - PAD - 20),
              "github.com/iamkarp/bio-study-tutor",
              font=f_url, fill=MUTED)

    canvas.save(OUT, format="PNG", optimize=True)
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()
