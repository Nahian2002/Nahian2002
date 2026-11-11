#!/usr/bin/env python3
"""Render GitHub-profile-ready CORE/LAB double-orbit hero animations.

Each ellipse revolves at a different angular velocity. Each electron
simultaneously moves around its own tilted orbit with a separate speed.
All paths are periodic and match seamlessly across the four-second loop.

Outputs animated 60 FPS WebP with a 50 FPS GIF fallback (GIF timing is 10ms).
"""
from __future__ import annotations

import io
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image
from render_featured_atom import create_webp, create_gif

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", "http://www.w3.org/2000/svg")

FRAMES = 240
ORIGIN_X, ORIGIN_Y = 1056, 182
RX, RY = 154, 56
BASE_DEGREES = [-27.0, 38.0, 89.0]
ORBIT_TURNS = [1, -1, 2]
ELECTRON_TURNS = [3, -4, 5]
PHASES = [0.07, 0.37, 0.71]


def find_one(root: ET.Element, css_class: str, idx: int | None = None) -> ET.Element:
    found = [
        node for node in root.iter()
        if css_class in node.get("class", "").split()
        and (idx is None or node.get("data-index") == str(idx))
    ]
    if len(found) != 1:
        raise AssertionError(f"Need one {css_class}[{idx}], got {len(found)}")
    return found[0]


def point(angle_degrees: float, phase_turns: float) -> tuple[float, float]:
    theta = 2 * math.pi * phase_turns
    rot = math.radians(angle_degrees)
    a = RX * math.cos(theta)
    b = RY * math.sin(theta)
    return (
        ORIGIN_X + a * math.cos(rot) - b * math.sin(rot),
        ORIGIN_Y + a * math.sin(rot) + b * math.cos(rot),
    )


def update(root: ET.Element, frame: int) -> None:
    t = frame / FRAMES

    # Triple ring rotation: +360, -360 and +720 deg per four-second loop.
    # Electron motion is calculated separately in each ring's rotating frame.
    for idx in range(3):
        twist = 2 * math.sin(2 * math.pi * t + idx * 2 * math.pi / 3)
        angle = BASE_DEGREES[idx] + ORBIT_TURNS[idx] * 360 * t + twist
        ring = find_one(root, "hero-orbit", idx)
        ring.set("transform", f"rotate({angle:.4f} {ORIGIN_X} {ORIGIN_Y})")

        phase = PHASES[idx] + ELECTRON_TURNS[idx] * t
        x, y = point(angle, phase)
        electron = find_one(root, "hero-electron", idx)
        halo = find_one(root, "hero-electron-glow", idx)
        electron.set("cx", f"{x:.3f}")
        electron.set("cy", f"{y:.3f}")
        halo.set("cx", f"{x:.3f}")
        halo.set("cy", f"{y:.3f}")
        halo.set("r", f"{13 + 1.8 * math.sin(2 * math.pi * (t + idx / 3)):.3f}")

        # Both trails are behind the electron and lie on its present orbit.
        for lag, distance in ((1, 2), (2, 5)):
            trail = [
                node for node in root.iter()
                if "hero-trail" in node.get("class", "").split()
                and node.get("data-index") == str(idx)
                and node.get("data-lag") == str(lag)
            ]
            if len(trail) != 1:
                raise AssertionError(f"Missing trail: electron={idx}, lag={lag}")
            px, py = point(angle, phase - ELECTRON_TURNS[idx] * distance / FRAMES)
            trail[0].set("cx", f"{px:.3f}")
            trail[0].set("cy", f"{py:.3f}")

    guide = find_one(root, "hero-guide")
    guide.set("stroke-dashoffset", f"{36 * t:.3f}")
    nucleus = find_one(root, "hero-nucleus-halo")
    nucleus.set("r", f"{76 + 2 * math.sin(2 * math.pi * t):.3f}")
    nucleus.set("opacity", f"{0.065 + .03 * (0.5 + 0.5 * math.cos(2 * math.pi * t)):.3f}")
    for dot in root.iter():
        if "blink" in dot.get("class", "").split():
            dot.set("opacity", f"{.52 + .48 * (0.5 + 0.5 * math.sin(2 * math.pi * t)):.3f}")


def render(color: str, width: int = 960) -> None:
    file = ASSETS / f"hero-premium-{color}.svg"
    root = ET.parse(file).getroot()
    for style in list(root.findall(".//" + NS + "style")):
        # CSS can overwrite per-frame transforms in some SVG renderers.
        for parent in root.iter():
            if style in list(parent):
                parent.remove(style)
                break

    if not any(node.text == "CORE" for node in root.iter(NS + "text")):
        raise AssertionError("The hero must display CORE rather than J/N")
    h = round(width * 390 / 1280)
    frames = []
    for idx in range(FRAMES):
        update(root, idx)
        data = cairosvg.svg2png(
            bytestring=ET.tostring(root, encoding="utf-8"),
            output_width=width,
            output_height=h,
        )
        frames.append(Image.open(io.BytesIO(data)).convert("RGB"))

    create_webp(frames, ASSETS / f"hero-core-double-spin-{color}.webp")
    create_gif(frames, ASSETS / f"hero-core-double-spin-{color}.gif")
    print(f"PASS {color}: 3 rotating rings + 3 independent electrons, {width}x{h}")


if __name__ == "__main__":
    render("dark")
    render("light")
