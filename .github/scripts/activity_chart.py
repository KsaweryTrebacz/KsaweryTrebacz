"""Generuje wykres kontrybucji z ostatniego roku (SVG) w palecie profilu.

Dane pochodzą z publicznego kalendarza kontrybucji na GitHubie, więc skrypt nie potrzebuje
tokenu ani zewnętrznych bibliotek. Kolory są jednolite: czerń, biel, szarość i fiolet.

Uruchomienie:  python .github/scripts/activity_chart.py [użytkownik] [plik_wyjściowy]
Domyślny plik wyjściowy to out/aktywnosc.svg w katalogu repozytorium.
"""
from __future__ import annotations

import datetime as dt
import html
import math
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "out" / "aktywnosc.svg"

BG = "#15151D"
GRID = "#24242F"
STUB = "#2A2A35"
WHITE = "#F8FAFC"
GRAY = "#94A3B8"
GRAY_DARK = "#64748B"
VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
VIOLET_PALE = "#C4B5FD"

MONTHS = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
WEEKDAYS = ["pn", "wt", "śr", "cz", "pt", "sb", "nd"]
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

W, H = 900, 330
PAD = 28


def fetch(user: str) -> str:
    request = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme activity chart)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def parse(page: str) -> tuple[dict[dt.date, int], int | None]:
    """Zwraca liczbę kontrybucji dla każdego dnia oraz sumę z nagłówka kalendarza."""
    cell_dates: dict[str, dt.date] = {}
    for match in re.finditer(r"<td\b[^>]*\bContributionCalendar-day\b[^>]*>", page):
        tag = match.group(0)
        date = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        cell_id = re.search(r'\bid="([^"]+)"', tag)
        if date and cell_id:
            cell_dates[cell_id.group(1)] = dt.date.fromisoformat(date.group(1))

    counts: dict[dt.date, int] = {}
    for match in re.finditer(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        day = cell_dates.get(match.group(1))
        if day is None:
            continue
        number = re.match(r"\s*([\d,]+)\s+contribution", html.unescape(match.group(2)))
        counts[day] = int(number.group(1).replace(",", "")) if number else 0

    header = re.search(r"([\d,]+)\s+contributions?\s+in the last year", re.sub(r"\s+", " ", page))
    total = int(header.group(1).replace(",", "")) if header else None
    return dict(sorted(counts.items())), total


def nice_axis(maximum: int, ticks: int = 4) -> tuple[int, int]:
    raw = max(maximum, 1) / ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 5, 10) if raw <= m * magnitude)
    step = max(1, int(step))
    return step, step * math.ceil(max(maximum, 1) / step)


def days_word(n: int) -> str:
    return "dzień" if n == 1 else "dni"


def grow(attr: str, start: float, end: float, delay: float) -> str:
    """Animacja wzrostu słupka; przed startem słupek ma zerową wysokość, bez mignięcia."""
    return (
        f'<animate attributeName="{attr}" values="{start:.1f};{start:.1f};{end:.1f}" '
        f'keyTimes="0;{delay:.3f};1" dur="1.4s" fill="freeze" />'
    )


def render(counts: dict[dt.date, int], header_total: int | None) -> str:
    last_day = max(counts)
    weeks: dict[dt.date, int] = defaultdict(int)
    by_weekday = [0] * 7
    for day, n in counts.items():
        weeks[day - dt.timedelta(days=day.weekday())] += n
        by_weekday[day.weekday()] += n
    week_list = sorted(weeks.items())

    streak = best_streak = 0
    for day in sorted(counts):
        streak = streak + 1 if counts[day] > 0 else 0
        best_streak = max(best_streak, streak)

    total = header_total if header_total is not None else sum(counts.values())
    active_days = sum(1 for n in counts.values() if n > 0)
    best_week_start, best_week = max(week_list, key=lambda item: item[1])

    out: list[str] = []
    add = out.append
    add(
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Aktywność na GitHubie w ostatnim roku: {total} kontrybucji">'
    )
    add(f"<style>.t {{ font-family: {FONT}; }}</style>")
    add(f'<rect width="{W}" height="{H}" rx="20" fill="{BG}" />')

    # Nagłówek
    add(f'<text class="t" x="{PAD}" y="46" font-size="20" font-weight="700" fill="{VIOLET_LIGHT}">'
        "Aktywność w ostatnim roku</text>")
    add(f'<text class="t" x="{PAD}" y="68" font-size="12" fill="{GRAY_DARK}">'
        f"kontrybucje tygodniowo · stan na {last_day:%d.%m.%Y}</text>")

    stats = [
        (str(total), "kontrybucji"),
        (str(active_days), "aktywnych dni"),
        (f"{best_streak} {days_word(best_streak)}", "najdłuższa seria"),
        (str(best_week), "najlepszy tydzień"),
    ]
    for i, (value, label) in enumerate(stats):
        x = 452 + i * 105
        add(f'<text class="t" x="{x}" y="46" font-size="22" font-weight="800" fill="{WHITE}">{html.escape(value)}</text>')
        add(f'<text class="t" x="{x}" y="66" font-size="11" fill="{GRAY}">{html.escape(label)}</text>')
    add(f'<rect x="{PAD}" y="88" width="{W - 2 * PAD}" height="1" fill="{GRID}" />')

    # Wykres tygodniowy
    x0, x1, top, base = 60.0, 640.0, 118.0, 280.0
    step, axis_max = nice_axis(best_week)
    scale = (base - top) / axis_max
    for value in range(0, axis_max + 1, step):
        y = base - value * scale
        add(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="1" fill="{GRID}" />')
        add(f'<text class="t" x="{x0 - 10}" y="{y + 4:.1f}" font-size="10" fill="{GRAY_DARK}" '
            f'text-anchor="end">{value}</text>')

    slot = (x1 - x0) / len(week_list)
    bar_w = max(2.0, slot * 0.62)
    previous_month = None
    last_label_x = -100.0
    for i, (week_start, n) in enumerate(week_list):
        x = x0 + i * slot + (slot - bar_w) / 2
        delay = 0.55 * i / max(1, len(week_list) - 1)
        if n == 0:
            add(f'<rect x="{x:.1f}" y="{base - 2:.1f}" width="{bar_w:.1f}" height="2" rx="1" fill="{STUB}" />')
        else:
            h = max(3.0, n * scale)
            fill = VIOLET_PALE if week_start == best_week_start else VIOLET_LIGHT
            add(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="2" fill="{fill}">'
                f"{grow('height', 0, h, delay)}{grow('y', base, base - h, delay)}</rect>")
            if week_start == best_week_start:
                add(f'<text class="t" x="{x + bar_w / 2:.1f}" y="{base - h - 8:.1f}" font-size="10" '
                    f'font-weight="700" fill="{VIOLET_PALE}" text-anchor="middle">{n}</text>')
        month = (week_start + dt.timedelta(days=3)).month
        if month != previous_month:
            if previous_month is not None and x - last_label_x > 26:
                add(f'<text class="t" x="{x:.1f}" y="{base + 20:.1f}" font-size="11" fill="{GRAY_DARK}">'
                    f"{MONTHS[month - 1]}</text>")
                last_label_x = x
            previous_month = month

    # Dni tygodnia
    add(f'<rect x="664" y="108" width="1" height="{base + 20 - 108}" fill="{GRID}" />')
    add(f'<text class="t" x="688" y="122" font-size="12" font-weight="600" fill="{GRAY}">dni tygodnia</text>')
    top_day = max(by_weekday) or 1
    for i, value in enumerate(by_weekday):
        y = 140 + i * 21
        add(f'<text class="t" x="688" y="{y + 9}" font-size="11" fill="{GRAY_DARK}">{WEEKDAYS[i]}</text>')
        add(f'<rect x="712" y="{y}" width="124" height="10" rx="5" fill="{STUB}" />')
        if value:
            width = max(6.0, 124 * value / top_day)
            delay = 0.3 + 0.05 * i
            add(f'<rect x="712" y="{y}" width="{width:.1f}" height="10" rx="5" fill="{VIOLET}">'
                f"{grow('width', 0, width, delay)}</rect>")
        add(f'<text class="t" x="{W - PAD}" y="{y + 9}" font-size="11" font-weight="600" fill="{WHITE}" '
            f'text-anchor="end">{value}</text>')

    add("</svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    user = sys.argv[1] if len(sys.argv) > 1 else "KsaweryTrebacz"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT
    try:
        counts, header_total = parse(fetch(user))
        if len(counts) < 300:
            raise ValueError(f"kalendarz ma tylko {len(counts)} dni")
    except Exception as error:  # noqa: BLE001 - każdy błąd sieci lub formatu traktujemy tak samo
        if out.exists():
            print(f"::warning::Nie udało się odczytać kalendarza ({error}). Zostawiam poprzedni wykres.")
            return
        raise
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(counts, header_total), encoding="utf-8", newline="\n")
    print(f"Zapisano {out}: {len(counts)} dni, {sum(counts.values())} kontrybucji")


if __name__ == "__main__":
    main()
