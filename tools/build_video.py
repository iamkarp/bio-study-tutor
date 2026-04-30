#!/usr/bin/env python3
"""Build the Bio Study Tutor demo video.

Generates TTS audio for both speakers via Microsoft edge-tts (free, no API key),
then assembles screenshot + audio segments into a single MP4 with ffmpeg.

Voices:
    Maya (interviewer): en-US-AvaNeural (warm female, conversational)
    Jason (interviewee): en-US-AndrewNeural (warm male, conversational)

Usage:
    cd /Users/macbook/Documents/Study
    python3 tools/build_video.py
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts

REPO = Path(__file__).resolve().parents[1]
SHOTS = REPO / "screenshots"
VIDEO = REPO / "video"
AUDIO = VIDEO / "audio"
PARTS = VIDEO / "parts"
OUT = VIDEO / "bio_tutor_demo.mp4"

VOICE_MAYA = "en-US-AvaNeural"
VOICE_JASON = "en-US-AndrewNeural"
RATE = "+0%"


@dataclass
class Seg:
    speaker: str  # "maya" or "jason"
    text: str
    image: str   # screenshot filename


# (speaker, line, screenshot) — screenshot stays on the previous one until the cut
SCRIPT: list[Seg] = [
    # ── HOOK ─────────────────────────────────────────────────────────────
    Seg("maya",
        "Picture this. It's eleven p.m. A student's flying home for spring break, "
        "no Wi-Fi, exam in the morning. She's stuck on meiosis. What does she do?",
        "Study Guide.png"),
    Seg("jason",
        "A year ago — nothing. Today, she opens this. Bio 1320, every concept "
        "from her course, and a tutor that runs on her laptop. Offline. "
        "Powered by Gemma 4.",
        "Study Guide.png"),

    # ── DEMO: Study Guide ────────────────────────────────────────────────
    Seg("maya", "Walk me through what we built.",
        "Study Guide.png"),
    Seg("jason",
        "Two hundred and fifty four atomic pages, one per concept. Hyperlinked. "
        "Searchable. Browse by chapter, browse by topic. It's basically Wikipedia, "
        "but only what's on her exam.",
        "Study Guide.png"),

    # ── Ask ──────────────────────────────────────────────────────────────
    Seg("maya", "And the tutor part?",
        "ask a tutor.png"),
    Seg("jason",
        "Ask anything — and Gemma 4 answers. The trick is, it can only see the "
        "wiki. So no hallucinations. No made-up citations. If you ask about "
        "something not on the exam, it tells you.",
        "ask a tutor.png"),

    # ── Quiz / Flash / Match (rapid sequence) ────────────────────────────
    Seg("jason",
        "It quizzes her, generates new questions on demand, gives explanations.",
        "quiz.png"),
    Seg("jason", "Flashcards she can flip.",
        "flash cards.png"),
    Seg("jason", "A match game.",
        "match game.png"),
    Seg("jason",
        "And a four-page printable cheat sheet for the morning of the exam.",
        "quick refernce guide.png"),

    # ── Knowledge Graph ──────────────────────────────────────────────────
    Seg("maya", "And this?",
        "graph network.png"),
    Seg("jason",
        "A knowledge graph. Click any concept — and you see what it depends on, "
        "what it leads to, what it's compared to. Two degrees of neighbors stay "
        "in color. Everything else fades. It's a way to navigate the course by "
        "relationships, not just by chapter.",
        "graph network.png"),

    # ── IMPACT ───────────────────────────────────────────────────────────
    Seg("maya",
        "Okay, but here's the part I want to understand. What makes this "
        "different from ChatGPT?",
        "Study Guide.png"),
    Seg("jason",
        "Three things. One — it's grounded. Every answer comes from the wiki, "
        "every wiki page cites its source slide. If the textbook is wrong, you "
        "can find where. ChatGPT can't do that. Two — it's free. Gemma 4 runs "
        "locally on a laptop with twenty-four gigs of RAM. There is no "
        "subscription, no per-token bill, no API key.",
        "Study Guide.png"),
    Seg("maya", "And three?",
        "Study Guide.png"),
    Seg("jason",
        "It's private. Her questions never leave her laptop. That matters for "
        "I-E-P students, for kids studying mental health topics, for any student "
        "in a school that won't whitelist OpenAI. The cloud is not the problem. "
        "Trusting the cloud is the problem.",
        "Study Guide.png"),

    # ── VISION ───────────────────────────────────────────────────────────
    Seg("maya", "What scales?",
        "graph network.png"),
    Seg("jason",
        "The pattern. We open-sourced a tool that turns any folder of slides "
        "into this. Calculus. Anatomy. Organic chem. The bar exam. A few hours "
        "of work and any subject has its own private tutor — running on hardware "
        "students already own.",
        "graph network.png"),

    # ── CLOSE ────────────────────────────────────────────────────────────
    Seg("jason",
        "The student who already has the most expensive private tutor in their "
        "school district sets the upper bound on how good education has to get "
        "before AI levels the playing field. With Gemma 4, that bound just "
        "collapsed.",
        "Study Guide.png"),
    Seg("maya",
        "A tutor for every course. I love it. Where can people see it?",
        "Study Guide.png"),
    Seg("jason",
        "Link's in the description. Clone the repo, run it locally, build your own.",
        "Study Guide.png"),
    Seg("maya", "Thanks, Jason.",
        "Study Guide.png"),
    Seg("jason", "Thanks for having me.",
        "Study Guide.png"),
]


# ── Audio generation ─────────────────────────────────────────────────────
async def synthesize(text: str, voice: str, out: Path) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=RATE)
    await communicate.save(str(out))


async def build_audio(segments: list[Seg]) -> list[Path]:
    AUDIO.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for i, seg in enumerate(segments, start=1):
        voice = VOICE_MAYA if seg.speaker == "maya" else VOICE_JASON
        out = AUDIO / f"{i:02d}_{seg.speaker}.mp3"
        if not out.exists() or out.stat().st_size < 1000:
            print(f"  TTS [{i:02d}] {seg.speaker}: {len(seg.text)} chars → {out.name}")
            await synthesize(seg.text, voice, out)
        else:
            print(f"  cached  [{i:02d}] {out.name}")
        files.append(out)
    return files


# ── ffmpeg helpers ───────────────────────────────────────────────────────
def _ff() -> str:
    for cand in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if Path(cand).exists():
            return cand
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError("ffmpeg not found. Install via `brew install ffmpeg`.")


def make_segment(image: Path, audio: Path, out: Path) -> None:
    cmd = [
        _ff(), "-y",
        "-loop", "1", "-i", str(image),
        "-i", str(audio),
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#0f172a",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def concat_segments(parts: list[Path], out: Path) -> None:
    manifest = PARTS / "concat.txt"
    manifest.write_text("\n".join(f"file '{p.resolve()}'" for p in parts))
    cmd = [
        _ff(), "-y",
        "-f", "concat", "-safe", "0", "-i", str(manifest),
        "-c", "copy",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def main() -> None:
    print(f"Building {len(SCRIPT)} segments…\n")

    # 1. TTS audio
    print("→ Generating TTS audio (edge-tts)")
    audio_files = asyncio.run(build_audio(SCRIPT))
    print(f"  done ({len(audio_files)} audio clips)\n")

    # 2. Per-segment video clips
    print("→ Building per-segment video clips (ffmpeg)")
    PARTS.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for i, (seg, audio) in enumerate(zip(SCRIPT, audio_files), start=1):
        image = SHOTS / seg.image
        if not image.exists():
            raise FileNotFoundError(f"missing screenshot: {image}")
        out = PARTS / f"seg_{i:02d}.mp4"
        if not out.exists():
            print(f"  seg [{i:02d}] {seg.speaker:6s} · {seg.image} → {out.name}")
            make_segment(image, audio, out)
        else:
            print(f"  cached  seg [{i:02d}] {out.name}")
        parts.append(out)
    print(f"  done ({len(parts)} segments)\n")

    # 3. Concat
    print("→ Concatenating segments → final MP4")
    concat_segments(parts, OUT)
    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"  ✓ wrote {OUT.relative_to(REPO)} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
