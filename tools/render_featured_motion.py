#!/usr/bin/env python3
"""Render GitHub-compatible GIFs from the existing featured-card SVG artwork.

GitHub does not reliably play inline CSS animations in profile SVG previews.
These GIFs preserve the existing card designs and animate only their icons.
Use: python tools/render_featured_motion.py
"""
from __future__ import annotations

import io
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")
FRAMES = 96
DURATION_MS = 40  # 25 FPS; same 3.84-second seamless cycle as the previous 24-frame GIFs


def icon_group(root: ET.Element, index: int) -> ET.Element:
    groups = [
        item for item in root.iter(NS + "g")
        if item.get("transform", "").startswith("translate(")
        and "scale(0.62)" in item.get("transform", "")
    ]
    if len(groups) != 4:
        raise ValueError(f"Expected exactly four project icons, got {len(groups)}")
    return groups[index]


def by_class(parent: ET.Element, class_name: str) -> list[ET.Element]:
    return [
        item for item in parent.iter()
        if class_name in item.get("class", "").split()
    ]


def apply_frame(root: ET.Element, frame: int) -> None:
    # All motions return to their initial state at the loop boundary.
    t = frame / FRAMES
    music = icon_group(root, 0)
    waves = by_class(music, "nw-wave")
    if len(waves) != 5:
        raise ValueError("Five separate NightWave equalizer bars required")
    xs = [-55, -27, 0, 27, 55]
    heights = [27, 52, 70, 47, 23]
    for i, path in enumerate(waves):
        modulation = 0.57 + 0.43 * (0.5 + 0.5 * math.sin(2 * math.pi * (t - i / 5)))
        half_height = heights[i] * modulation
        path.set("d", f"M{xs[i]} {-half_height:.2f}V{half_height:.2f}")

    assistant = icon_group(root, 1)
    spokes = by_class(assistant, "cosmo-spokes")
    centers = by_class(assistant, "cosmo-core")
    if len(spokes) != 1 or len(centers) != 1:
        raise ValueError("COSMO spokes and core not found")
    # Eight-way symmetrical spokes make 45 degrees a seamless full cycle.
    spokes[0].set("transform", f"rotate({45 * t:.2f})")
    centers[0].set("opacity", f"{0.76 + 0.24 * (0.5 + 0.5 * math.cos(2 * math.pi * t)):.3f}")

    server = icon_group(root, 2)
    leds = by_class(server, "server-led")
    if len(leds) != 3:
        raise ValueError("Three HomeLab status lights required")
    for i, led in enumerate(leds):
        pulse = 0.32 + 0.68 * (0.5 + 0.5 * math.cos(2 * math.pi * (t - i / 3)))
        led.set("opacity", f"{pulse:.3f}")

    world = icon_group(root, 3)
    meridian = by_class(world, "cenqro-meridian")
    latitude = by_class(world, "cenqro-latitude")
    point = by_class(world, "cenqro-point")
    if len(meridian) != 1 or len(latitude) != 1 or len(point) != 1:
        raise ValueError("CENQRO globe layers not found")
    meridian[0].set("rx", f"{12 + 33 * math.cos(2 * math.pi * t) ** 2:.2f}")
    latitude[0].set("transform", f"rotate({7 * math.sin(2 * math.pi * t):.2f})")
    point[0].set("r", f"{7 + 2 * (0.5 + 0.5 * math.sin(2 * math.pi * t)):.2f}")


def render(source: str, destination: str, width: int) -> None:
    doc = ET.parse(ASSETS / source)
    root = doc.getroot()
    # Embedded CSS animation is not required for frame rendering; it can
    # override per-frame values in some SVG renderer implementations.
    for style in list(root.findall(NS + "style")):
        root.remove(style)

    height = int(round(width * int(root.get("height")) / int(root.get("width"))))
    frames: list[Image.Image] = []
    for i in range(FRAMES):
        apply_frame(root, i)
        png = cairosvg.svg2png(
            bytestring=ET.tostring(root, encoding="utf-8"),
            output_width=width,
            output_height=height,
        )
        frames.append(Image.open(io.BytesIO(png)).convert("RGB"))

    # A shared palette prevents frame-to-frame color and text flicker.
    palette = frames[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    output = ASSETS / destination
    indexed[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=1,
    )

    with Image.open(output) as check:
        if check.n_frames != FRAMES or check.info.get("loop") != 0:
            raise AssertionError(f"GIF loop/frame validation failed: {destination}")
        # Verify the actual encoded delay instead of assuming Pillow honored it.
        for index in range(FRAMES):
            check.seek(index)
            if check.info.get("duration") != DURATION_MS:
                raise AssertionError(f"Incorrect frame delay at {index} for {destination}")
    if output.stat().st_size > 2_000_000:
        raise AssertionError(f"GIF unexpectedly exceeds 2 MB: {destination}")
    print(f"OK: {destination} ({width}x{height}, {FRAMES} frames, "
          f"{DURATION_MS}ms/frame, {output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    render("featured-public-desktop.svg", "featured-ultrasmooth-desktop.gif", 960)
    render("featured-public-mobile.svg", "featured-ultrasmooth-mobile.gif", 525)
