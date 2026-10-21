"""Generuje assets/technologie.svg: zaokrąglone chipy technologii w palecie profilu.

Listę technologii zmieniasz w CATEGORIES poniżej, a potem uruchamiasz:
    python .github/scripts/tech_chips.py
Ikony marek pochodzą z pakietu simple-icons (wersja przypięta w ICONS_VERSION).
Druga wartość w parze to nazwa ikony z simple-icons.org albo None, gdy chip ma być bez ikony.
"""
from __future__ import annotations

import html
import re
import urllib.request
from pathlib import Path

CATEGORIES: list[tuple[str, list[tuple[str, str | None]]]] = [
    ("Języki", [
        ("Python", "python"), ("R", "r"), ("C++", "cplusplus"), ("SQL", "mysql"),
        ("HTML", "html5"), ("CSS", "css"), ("JavaScript", "javascript"),
    ]),
    ("Dane i ML", [
        ("pandas", "pandas"), ("NumPy", "numpy"), ("scikit-learn", "scikitlearn"),
        ("TensorFlow", "tensorflow"), ("OpenCV", "opencv"), ("Jupyter", "jupyter"),
        ("tidyverse", "tidyverse"), ("tidymodels", None), ("XGBoost", None),
    ]),
    ("AI", [
        ("Whisper", None), ("Phi", None), ("Azure AI Speech", None), ("Azure OpenAI", None),
    ]),
    ("Testy", [
        ("pytest", "pytest"), ("Selenium", "selenium"),
    ]),
    ("Narzędzia", [
        ("Git", "git"), ("GitHub", "github"), ("RStudio", "rstudioide"),
        ("MySQL Workbench", "mysql"), ("Pygame", None),
    ]),
]

ICONS_VERSION = "16.35.0"
OUT = Path(__file__).resolve().parents[2] / "assets" / "technologie.svg"

BG = "#15151D"
CHIP = "#1C1C26"
CHIP_STROKE = "#2A2A35"
LINE = "#24242F"
WHITE = "#F8FAFC"
VIOLET_LIGHT = "#A78BFA"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

W = 900
PAD = 28
CHIPS_X = 176
CHIP_H = 34
GAP_X = 8
GAP_Y = 8
ROW_GAP = 18
ICON = 15


def icon_path(slug: str) -> str:
    url = f"https://cdn.jsdelivr.net/npm/simple-icons@{ICONS_VERSION}/icons/{slug}.svg"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-readme"}), timeout=20) as r:
        svg = r.read().decode("utf-8")
    match = re.search(r'<path d="([^"]+)"', svg)
    if not match:
        raise ValueError(f"Brak ścieżki w ikonie {slug}")
    return match.group(1)


def text_width(text: str) -> float:
    """Przybliżona szerokość tekstu 13 px (półgruby); textLength wyrównuje resztę."""
    width = 0.0
    for ch in text:
        if ch in "iljtfrI.,'-|!:;":
            width += 4.2
        elif ch in "mwMW":
            width += 11.0
        elif ch == " ":
            width += 3.8
        elif ch.isupper():
            width += 8.6
        elif ch.isdigit():
            width += 7.4
        else:
            width += 7.2
    return width


def render() -> str:
    paths = {slug: icon_path(slug) for _, items in CATEGORIES for _, slug in items if slug}
    body: list[str] = []
    y = PAD
    for index, (label, items) in enumerate(CATEGORIES):
        if index:
            body.append(f'<rect x="{PAD}" y="{y - ROW_GAP / 2:.1f}" width="{W - 2 * PAD}" height="1" fill="{LINE}" />')
        x, line_top = CHIPS_X, y
        for name, slug in items:
            tw = text_width(name)
            cw = 14 + (ICON + 8 if slug else 0) + tw + 14
            if x + cw > W - PAD:
                x, line_top = CHIPS_X, line_top + CHIP_H + GAP_Y
            body.append(f'<rect x="{x + 0.5:.1f}" y="{line_top + 0.5:.1f}" width="{cw - 1:.1f}" height="{CHIP_H - 1}" '
                        f'rx="{(CHIP_H - 1) / 2}" fill="{CHIP}" stroke="{CHIP_STROKE}" />')
            tx = x + 14
            if slug:
                scale = ICON / 24
                body.append(f'<path transform="translate({tx:.1f} {line_top + (CHIP_H - ICON) / 2:.1f}) scale({scale:.4f})" '
                            f'fill="{VIOLET_LIGHT}" d="{paths[slug]}" />')
                tx += ICON + 8
            body.append(f'<text class="t" x="{tx:.1f}" y="{line_top + 22:.1f}" font-size="13" font-weight="600" '
                        f'fill="{WHITE}" textLength="{tw:.1f}" lengthAdjust="spacing">{html.escape(name)}</text>')
            x += cw + GAP_X
        row_bottom = line_top + CHIP_H
        label_y = y + (row_bottom - y) / 2 + 5
        body.append(f'<text class="t" x="{PAD}" y="{label_y:.1f}" font-size="14" font-weight="700" '
                    f'fill="{VIOLET_LIGHT}">{html.escape(label)}</text>')
        y = row_bottom + ROW_GAP
    height = y - ROW_GAP + PAD
    head = (f'<svg width="{W}" height="{height:.0f}" viewBox="0 0 {W} {height:.0f}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="Technologie: ' +
            html.escape(", ".join(name for _, items in CATEGORIES for name, _ in items)) + '">')
    return "\n".join([
        head,
        f"<style>.t {{ font-family: {FONT}; }}</style>",
        f'<rect width="{W}" height="{height:.0f}" rx="20" fill="{BG}" />',
        *body,
        "</svg>",
    ]) + "\n"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"Zapisano {OUT}")


if __name__ == "__main__":
    main()
