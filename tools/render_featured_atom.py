#!/usr/bin/env python3
"""Render real motion files for GitHub's four-card profile showcase.

APNG plays at an exact rational 60 FPS; GIF fallback uses reliable 50 FPS
because GIF frame delays have 10 ms resolution. No browser scripts required.
"""
from __future__ import annotations

import io
import math
import struct
import zlib
from pathlib import Path
import xml.etree.ElementTree as ET
import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")
FRAMES = 240
FPS = 60
FALLBACK_FPS = 50
GIF_DELAY = 20


def group(root: ET.Element, index: int) -> ET.Element:
    groups = [
        el for el in root.iter(NS + "g")
        if el.get("transform", "").startswith("translate(")
        and "scale(0.62)" in el.get("transform", "")
    ]
    if len(groups) != 4:
        raise ValueError(f"Expected four card icons, got {len(groups)}")
    return groups[index]


def named(node: ET.Element, name: str) -> ET.Element:
    matches = [el for el in node.iter() if name in el.get("class", "").split()]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one SVG element with class {name}")
    return matches[0]


def frame(root: ET.Element, i: int) -> None:
    t = i / FRAMES  # four seconds, periodic continuous motion

    # NightWave: five gentle phase-shifted oscillations.
    music = group(root, 0)
    bars = [
        el for el in music.iter()
        if "nw-wave" in el.get("class", "").split()
    ]
    if len(bars) != 5:
        raise ValueError("Missing equalizer bars")
    for n, (bar, x, tall) in enumerate(zip(
        bars, (-55, -27, 0, 27, 55), (27, 52, 70, 47, 23)
    )):
        amplitude = 0.57 + 0.43 * (0.5 + 0.5 * math.sin(
            2 * math.pi * (t - n / 5)))
        h = tall * amplitude
        bar.set("d", f"M{x} {-h:.3f}V{h:.3f}")

    # COSMO: rotating spokes, breathing nucleus.
    cosmo = group(root, 1)
    named(cosmo, "cosmo-spokes").set(
        "transform", f"rotate({45 * t:.4f})"
    )
    named(cosmo, "cosmo-core").set(
        "opacity", f"{0.76 + 0.24 * (0.5 + 0.5 * math.cos(2 * math.pi * t)):.3f}"
    )

    # HomeLab: staggered status-light pulses.
    lab = group(root, 2)
    leds = [
        el for el in lab.iter()
        if "server-led" in el.get("class", "").split()
    ]
    if len(leds) != 3:
        raise ValueError("Missing HomeLab LEDs")
    for n, led in enumerate(leds):
        pulse = 0.32 + 0.68 * (0.5 + 0.5 * math.cos(
            2 * math.pi * (t - n / 3)))
        led.set("opacity", f"{pulse:.3f}")

    # CENQRO: three orbital planes, 3 particles and a pulsing nucleus.
    atom = group(root, 3)
    named(atom, "atom-glow").set(
        "r", f"{19 + 4 * (0.5 + 0.5 * math.sin(2 * math.pi * t)):.3f}"
    )
    named(atom, "atom-core").set(
        "r", f"{8 + (0.5 + 0.5 * math.cos(2 * math.pi * t)):.3f}"
    )
    for n, (tilt, turns) in enumerate(((0.0, 1), (60.0, -2), (120.0, 3))):
        wobble = 2.5 * math.sin(2 * math.pi * t + n * 2 * math.pi / 3)
        rot = math.radians(tilt + wobble)
        named(atom, f"atom-orbit-{n}").set(
            "transform", f"rotate({tilt + wobble:.3f})"
        )
        phase = 2 * math.pi * (turns * t + n / 3)
        px, py = 77 * math.cos(phase), 30 * math.sin(phase)
        electron = named(atom, f"atom-electron-{n}")
        electron.set("cx", f"{px * math.cos(rot) - py * math.sin(rot):.3f}")
        electron.set("cy", f"{px * math.sin(rot) + py * math.cos(rot):.3f}")
        electron.set(
            "opacity", f"{0.75 + 0.25 * (0.5 + 0.5 * math.sin(phase)):.3f}"
        )


def create_apng(images: list[Image.Image], output: Path) -> None:
    images[0].save(
        output, format="PNG", save_all=True, append_images=images[1:],
        loop=0, duration=17, optimize=True, compress_level=7,
        disposal=0, blend=0,
    )
    # APNG delay is a rational (num/den). Write exactly 1/60 second.
    content = bytearray(output.read_bytes())
    offset = 8
    controls = 0
    while offset + 12 <= len(content):
        length = struct.unpack_from(">I", content, offset)[0]
        name = bytes(content[offset + 4:offset + 8])
        data_end = offset + 8 + length
        if name == b"fcTL":
            if length != 26:
                raise AssertionError("Unexpected APNG frame-control size")
            content[offset + 28:offset + 32] = struct.pack(">HH", 1, FPS)
            crc = zlib.crc32(content[offset + 4:data_end]) & 0xFFFFFFFF
            struct.pack_into(">I", content, data_end, crc)
            controls += 1
        offset = data_end + 4
        if name == b"IEND":
            break
    if controls != FRAMES:
        raise AssertionError(f"APNG controls: {controls}, expected {FRAMES}")
    output.write_bytes(content)
    with Image.open(output) as check:
        if check.n_frames != FRAMES or check.info.get("loop") != 0:
            raise AssertionError("APNG loop/frame verification failed")
    print(f"PASS APNG {output.name}: {FRAMES} frames; 1/{FPS}s each; {output.stat().st_size:,} bytes")


def create_gif(images: list[Image.Image], output: Path) -> None:
    count = 4 * FALLBACK_FPS
    palette = images[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    selected = [
        images[round(i * FRAMES / count)].quantize(
            palette=palette, dither=Image.Dither.NONE
        )
        for i in range(count)
    ]
    selected[0].save(
        output, format="GIF", save_all=True, append_images=selected[1:],
        loop=0, duration=GIF_DELAY, optimize=True, disposal=1,
    )
    with Image.open(output) as check:
        if check.n_frames != count or check.info.get("loop") != 0:
            raise AssertionError("GIF frame/loop verification failed")
        for i in range(count):
            check.seek(i)
            if check.info.get("duration") != GIF_DELAY:
                raise AssertionError(f"Wrong fallback GIF frame delay at {i}")
    print(f"PASS GIF {output.name}: {count} frames; {GIF_DELAY}ms each; {output.stat().st_size:,} bytes")


def render(source: str, stem: str, width: int) -> None:
    root = ET.parse(ASSETS / source).getroot()
    for style in list(root.findall(NS + "style")):
        root.remove(style)
    h = round(width * int(root.get("height")) / int(root.get("width")))
    images: list[Image.Image] = []
    for i in range(FRAMES):
        frame(root, i)
        png = cairosvg.svg2png(
            bytestring=ET.tostring(root, encoding="utf-8"),
            output_width=width, output_height=h,
        )
        images.append(Image.open(io.BytesIO(png)).convert("RGB"))
    create_apng(images, ASSETS / f"{stem}.png")
    create_gif(images, ASSETS / f"{stem}.gif")
    print(f"PASS original card layout: {width}x{h}")


if __name__ == "__main__":
    render("featured-public-desktop.svg", "featured-atom60-desktop", 960)
    render("featured-public-mobile.svg", "featured-atom60-mobile", 525)
