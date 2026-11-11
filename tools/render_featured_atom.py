#!/usr/bin/env python3
"""Render real motion files for GitHub's four-card profile showcase.

Animated WebP targets 60 FPS with millisecond-accurate pacing; GIF fallback is 50 FPS
because GIF frame delays have 10 ms resolution. No browser scripts required.
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


def create_webp(images: list[Image.Image], output: Path) -> None:
    # 240 frames / 4000 ms = an average of 60 FPS. WebP supports
    # millisecond-exact timing; [17, 16, 17] style pacing avoids
    # GIF's 10ms resolution and browser clamping.
    durations = [
        round((i + 1) * 1000 / FPS) - round(i * 1000 / FPS)
        for i in range(FRAMES)
    ]
    if sum(durations) != 4000 or set(durations) != {16, 17}:
        raise AssertionError("Unexpected 60 FPS WebP timing")
    images[0].save(
        output, format="WEBP", save_all=True,
        append_images=images[1:], duration=durations, loop=0,
        quality=86, method=5, minimize_size=True, allow_mixed=True,
    )
    # Verify the actual WebP animation frame headers and timings.
    content = output.read_bytes()
    if content[:4] != b"RIFF" or content[8:12] != b"WEBP":
        raise AssertionError("Invalid RIFF/WebP file")
    pos, found = 12, []
    while pos + 8 <= len(content):
        name = content[pos:pos + 4]
        length = struct.unpack_from("<I", content, pos + 4)[0]
        if name == b"ANMF":
            found.append(int.from_bytes(content[pos + 20:pos + 23], "little"))
        pos += 8 + length + length % 2
    if found != durations:
        raise AssertionError(
            f"Encoded WebP timings differ: {len(found)} frames, "
            f"{sum(found)}ms vs expected {len(durations)} / 4000ms"
        )
    with Image.open(output) as check:
        if check.n_frames != FRAMES or check.info.get("loop") != 0:
            raise AssertionError("WebP frame/loop verification failed")
    if output.stat().st_size > 3_000_000:
        raise AssertionError("WebP too large for responsive profile")
    print(f"PASS WebP {output.name}: {FRAMES} frames / 60 FPS average "
          f"/ {output.stat().st_size:,} bytes")


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
    create_webp(images, ASSETS / f"{stem}.webp")
    create_gif(images, ASSETS / f"{stem}.gif")
    print(f"PASS original card layout: {width}x{h}")


if __name__ == "__main__":
    render("featured-public-desktop.svg", "featured-atom60-desktop", 960)
    render("featured-public-mobile.svg", "featured-atom60-mobile", 525)
