#!/usr/bin/env python3
"""Render the premium CORE/LAB GitHub profile hero (calm, floating V8).

The emblem gently floats vertically. Three orbit planes rotate slowly while
their electrons travel independently. The green SYSTEM ONLINE status LED
pulses directly in rendered frames (not via blocked SVG CSS).

Outputs native 1280x390 animated WebP at 60 FPS, with 50 FPS GIF fallback.
Both formats loop seamlessly after eight seconds and are dark/light aware.
"""
from __future__ import annotations

import io
import math
import struct
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")

FPS = 60
SECONDS = 8
FRAMES = FPS * SECONDS
FALLBACK_FPS = 50
WIDTH, HEIGHT = 1280, 390

X, Y, RX, RY = 1056, 182, 154, 56
BASE_ANGLES = (-27.0, 38.0, 89.0)
RING_DEGREES_PER_LOOP = (180.0, -180.0, 180.0)
ELECTRON_TURNS_PER_LOOP = (0.5, -0.5, 1.5)
PHASES = (0.08, 0.44, 0.73)


def named(root: ET.Element, cls: str, index: int | None = None) -> ET.Element:
    matches = [
        node for node in root.iter()
        if cls in node.get("class", "").split()
        and (index is None or node.get("data-index") == str(index))
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {cls}[{index}], found {len(matches)}")
    return matches[0]


def angle_at(i: int, t: float) -> float:
    # A tiny periodic tilt keeps motion natural without abrupt direction changes.
    return BASE_ANGLES[i] + RING_DEGREES_PER_LOOP[i] * t + 1.1 * math.sin(2 * math.pi * t)


def electron_at(i: int, t: float) -> tuple[float, float]:
    angle = math.radians(angle_at(i, t))
    phase = 2 * math.pi * (PHASES[i] + ELECTRON_TURNS_PER_LOOP[i] * t)
    px, py = RX * math.cos(phase), RY * math.sin(phase)
    return (
        X + px * math.cos(angle) - py * math.sin(angle),
        Y + px * math.sin(angle) + py * math.cos(angle),
    )


def check_seam() -> None:
    # Ellipse is 180-degree symmetric, so a half-turn in both the ring
    # and the electron phase returns to the exact initial appearance.
    for i in range(3):
        a, b = electron_at(i, 0), electron_at(i, 1)
        if math.dist(a, b) > 1e-6:
            raise AssertionError(f"Non-seamless electron orbit {i}")
        if (RING_DEGREES_PER_LOOP[i] / 180) % 1 != 0:
            raise AssertionError("Ring should return to equivalent ellipse orientation")
    assert math.isclose(4.5 * math.sin(2 * math.pi), 0, abs_tol=1e-8)


def frame(root: ET.Element, n: int) -> None:
    t = n / FRAMES

    # Float the entire emblem, including the core labels, only 4.5 px.
    field = root.find(".//" + NS + "g[@id='hero-core-orbit-field']")
    if field is None:
        raise AssertionError("Missing floating emblem group")
    field.set("transform", f"translate(0 {4.5 * math.sin(2 * math.pi * t):.3f})")

    for i in range(3):
        ring = named(field, "hero-orbit", i)
        ring.set("transform", f"rotate({angle_at(i, t):.4f} {X} {Y})")

        px, py = electron_at(i, t)
        electron = named(field, "hero-electron", i)
        glow = named(field, "hero-electron-glow", i)
        for item in (electron, glow):
            item.set("cx", f"{px:.3f}")
            item.set("cy", f"{py:.3f}")
        glow.set("r", f"{12 + .65 * math.sin(2 * math.pi * t + i):.3f}")
        glow.set("opacity", ".12")

        for lag in (1, 2):
            trail = [
                item for item in field.iter()
                if "hero-trail" in item.get("class", "").split()
                and item.get("data-index") == str(i)
                and item.get("data-lag") == str(lag)
            ]
            if len(trail) != 1:
                raise AssertionError(f"Missing electron {i} trail {lag}")
            tx, ty = electron_at(i, t - (7 if lag == 1 else 17) / FRAMES)
            trail[0].set("cx", f"{tx:.3f}")
            trail[0].set("cy", f"{ty:.3f}")

    named(field, "hero-guide").set("stroke-dashoffset", f"{13*t:.3f}")
    halo = named(field, "hero-nucleus-halo")
    halo.set("r", f"{76 + 1.6*math.sin(2*math.pi*t):.3f}")
    halo.set("opacity", f"{.07 + .015 * (1 + math.cos(2*math.pi*t)) / 2:.3f}")

    # Previously lost when CSS <style> was stripped by the raster renderer:
    # restore the gentle green LED pulse, plus a barely perceptible label glow.
    led = named(root, "blink")
    level = .28 + .72 * (1 + math.cos(4 * math.pi * t)) / 2
    led.set("opacity", f"{level:.3f}")
    labels = [
        el for el in root.iter(NS + "text") if (el.text or "").strip() == "SYSTEM ONLINE"
    ]
    if len(labels) != 1:
        raise AssertionError("Missing SYSTEM ONLINE label")
    labels[0].set("opacity", f"{.86 + .14 * (1 + math.cos(4 * math.pi * t)) / 2:.3f}")


def encode_webp(frames: list[Image.Image], output: Path) -> None:
    delays = [
        round((i + 1) * 1000 / FPS) - round(i * 1000 / FPS)
        for i in range(FRAMES)
    ]
    if sum(delays) != SECONDS * 1000 or set(delays) != {16, 17}:
        raise AssertionError("Unexpected 60-FPS frame timing")
    frames[0].save(
        output, format="WEBP", save_all=True, append_images=frames[1:],
        duration=delays, loop=0, quality=80, method=5,
        minimize_size=True, allow_mixed=True,
    )
    raw = output.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise AssertionError("Not a valid WebP")
    pos, actual = 12, []
    while pos + 8 <= len(raw):
        length = struct.unpack_from("<I", raw, pos + 4)[0]
        if raw[pos:pos+4] == b"ANMF":
            actual.append(int.from_bytes(raw[pos+20:pos+23], "little"))
        pos += 8 + length + length % 2
    if actual != delays:
        raise AssertionError(f"WebP timing mismatch, {len(actual)} decoded frames")
    with Image.open(output) as image:
        if image.n_frames != FRAMES or image.info.get("loop") != 0 or image.size != (WIDTH, HEIGHT):
            raise AssertionError("Invalid WebP frame count, loop or native dimensions")
    if output.stat().st_size > 6_000_000:
        raise AssertionError("WebP too large for profile")
    print(f"PASS {output.name}: native {WIDTH}x{HEIGHT}, {FRAMES} frames, 60 FPS, {output.stat().st_size:,} bytes", flush=True)


def encode_gif(frames: list[Image.Image], output: Path) -> None:
    count = SECONDS * FALLBACK_FPS
    palette = frames[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [
        frames[round(i * FRAMES / count)].quantize(palette=palette, dither=Image.Dither.NONE)
        for i in range(count)
    ]
    indexed[0].save(
        output, format="GIF", save_all=True, append_images=indexed[1:],
        loop=0, duration=20, optimize=True, disposal=1,
    )
    with Image.open(output) as image:
        if image.n_frames != count or image.info.get("loop") != 0 or image.size != (WIDTH, HEIGHT):
            raise AssertionError("Invalid fallback GIF frame count, loop or dimensions")
        for i in range(count):
            image.seek(i)
            if image.info.get("duration") != 20:
                raise AssertionError(f"GIF delay mismatch at frame {i}")
    if output.stat().st_size > 8_000_000:
        raise AssertionError("GIF fallback too large")
    print(f"PASS {output.name}: native {WIDTH}x{HEIGHT}, {count} frames, 50 FPS, {output.stat().st_size:,} bytes", flush=True)


def render(theme: str) -> None:
    root = ET.parse(ASSETS / f"hero-premium-{theme}.svg").getroot()
    # CSS animation is not dependable for externally embedded GitHub images.
    for parent in root.iter():
        for style in list(parent.findall(NS + "style")):
            parent.remove(style)
    labels = [(el.text or "").strip() for el in root.iter(NS + "text")]
    if "CORE" not in labels or "LAB" not in labels or "J/N" in labels:
        raise AssertionError("Incorrect CORE/LAB labels")
    if root.get("viewBox") != "0 0 1280 390":
        raise AssertionError("Hero dimensions unexpectedly changed")

    frames = []
    for i in range(FRAMES):
        frame(root, i)
        png = cairosvg.svg2png(
            bytestring=ET.tostring(root, encoding="utf-8"),
            output_width=WIDTH, output_height=HEIGHT,
        )
        frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
    stem = f"hero-core-calm-hires-{theme}"
    encode_webp(frames, ASSETS / f"{stem}.webp")
    encode_gif(frames, ASSETS / f"{stem}.gif")
    print(f"SUCCESS {theme} profile hero", flush=True)


if __name__ == "__main__":
    check_seam()
    render("dark")
    render("light")
