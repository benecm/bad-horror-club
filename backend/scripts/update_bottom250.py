"""Refresh app/data/bottom250.json from the public Letterboxd list.

The app never talks to Letterboxd itself; it reads this snapshot. Run by hand when you want to
pick up the list's weekly changes:

    uv run python scripts/update_bottom250.py

For offline use or tests, parse already-downloaded pages instead:

    uv run python scripts/update_bottom250.py --html-dir path/to/pages   # p1.html, p2.html, ...
"""

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

LIST_URL = "https://letterboxd.com/ur_mom_lol/list/letterboxds-bottom-250-horror-films/"
OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "bottom250.json"
EXPECTED = 250

# One <li> per film. The film data comes first and its list number last, so parse per item
# (never across items) to keep each film paired with its own number.
ITEM_BLOCK = re.compile(r'<li class="posteritem[^>]*>(.*?)</li>', re.S)
FIELD_NAME = re.compile(r'data-item-name="([^"]+)"')
FIELD_LINK = re.compile(r'data-item-link="([^"]+)"')
FIELD_NUMBER = re.compile(r'<p class="list-number">\s*(\d+)\s*</p>')
NAME = re.compile(r"^(.*) \((\d{4})\)$")


def parse_page(page: str) -> list[dict]:
    entries = []
    for block in ITEM_BLOCK.findall(page):
        name_m, link_m, number_m = (
            FIELD_NAME.search(block),
            FIELD_LINK.search(block),
            FIELD_NUMBER.search(block),
        )
        if not (name_m and link_m and number_m):
            continue
        number, name, link = number_m.group(1), name_m.group(1), link_m.group(1)
        name = html.unescape(name)
        m = NAME.match(name)
        title, year = (m.group(1), int(m.group(2))) if m else (name, None)
        entries.append(
            {
                "position": int(number),
                "title": title,
                "year": year,
                "letterboxd_url": f"https://letterboxd.com{link}",
            }
        )
    return entries


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "bad-horror-club-list-refresh/1.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html-dir", type=Path, help="parse p1.html, p2.html, ... from this folder")
    args = ap.parse_args()

    entries: list[dict] = []
    if args.html_dir:
        for path in sorted(args.html_dir.glob("p*.html")):
            entries += parse_page(path.read_text(encoding="utf-8"))
    else:
        page = 1
        while True:
            url = LIST_URL if page == 1 else f"{LIST_URL}page/{page}/"
            found = parse_page(fetch(url))
            if not found:
                break
            entries += found
            page += 1
            time.sleep(2)  # be polite

    positions = [e["position"] for e in entries]
    if positions != list(range(1, len(entries) + 1)) or len(entries) != EXPECTED:
        print(f"Unexpected list shape ({len(entries)} entries); not writing.", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": LIST_URL,
                "fetched_on": date.today().isoformat(),
                "films": entries,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} films to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
