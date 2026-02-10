"""
Competition master updater (hybrid).

Base template: data/competitions_base.json
Official site auto-fill: logo_url / official_sites (og:url) when available.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
BASE_JSON = DATA_DIR / "competitions_base.json"
OUT_JSON = DATA_DIR / "competitions.json"


def _fetch_official_meta(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    def meta(prop: str) -> str:
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            return tag["content"].strip()
        return ""

    og_title = meta("og:title")
    og_image = meta("og:image")
    og_url = meta("og:url")

    # favicon fallback
    icon = ""
    icon_tag = soup.find("link", rel=lambda v: v and "icon" in v.lower())
    if icon_tag and icon_tag.get("href"):
        icon = icon_tag["href"].strip()

    return {
        "og_title": og_title,
        "og_image": og_image,
        "og_url": og_url,
        "icon": icon,
    }


def update_competitions(only: List[str] | None = None) -> None:
    if not BASE_JSON.exists():
        raise FileNotFoundError(f"competitions_base.json not found: {BASE_JSON}")

    with BASE_JSON.open("r", encoding="utf-8") as f:
        competitions = json.load(f)

    for comp in competitions:
        comp_id = comp.get("id", "")
        if only and comp_id not in only:
            continue

        official_sites = comp.get("official_sites") or []
        if not official_sites:
            continue

        meta = None
        official_url = ""
        for candidate in official_sites:
            try:
                meta = _fetch_official_meta(candidate)
                official_url = candidate
                break
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️  {comp_id}: 公式サイト取得失敗 ({candidate}): {exc}")

        if meta is None:
            continue

        # Append og:url if present
        og_url = meta.get("og_url")
        if og_url and og_url not in official_sites:
            official_sites.append(og_url)
            comp["official_sites"] = official_sites

        # Fill logo_url if missing
        if not comp.get("logo_url"):
            logo_url = meta.get("og_image") or meta.get("icon")
            if logo_url:
                comp["logo_url"] = logo_url

        # Clear dynamic fields (managed elsewhere)
        comp["teams"] = []
        comp["data_summary"] = {
            "match_count": 0,
            "seasons": [],
            "date_range": {"start": "", "end": ""},
            "last_updated": "",
        }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(competitions, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("✅ competitions.json 更新完了")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Update competitions.json from base template + official site metadata.")
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated competition IDs to update (e.g., premier,urc,m6n).",
    )
    args = parser.parse_args(argv)

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    update_competitions(only)


if __name__ == "__main__":
    main()
