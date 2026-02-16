"""
Official team master updater.

This service updates data/teams.json from official team list sources,
independent of match data.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.collectors.international.six_nations import (
    SixNationsScraper,
    SixNationsWomensScraper,
    SixNationsU20Scraper,
)
from src.collectors.domestic.league_one_divisions import LeagueOneDivisionsScraper
from src.services.team_service import (
    generate_team_master,
    load_existing_teams,
    detect_duplicates,
)
from src.collectors.base import BaseScraper

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
TEAMS_SOURCES = DATA_DIR / "teams_sources.json"
TEAMS_JSON = DATA_DIR / "teams.json"


def _load_sources() -> Dict[str, dict]:
    if not TEAMS_SOURCES.exists():
        raise FileNotFoundError(f"teams_sources.json not found: {TEAMS_SOURCES}")
    with TEAMS_SOURCES.open("r", encoding="utf-8") as f:
        return json.load(f)


def _fetch_html(url: str) -> BeautifulSoup:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _fetch_html_selenium(url: str) -> BeautifulSoup:
    BaseScraper._prefer_selenium_manager()
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(120)
    try:
        driver.get(url)
        # Basic readiness
        WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
        # Site-specific waits
        if "super.rugby" in url and "/teams" in url:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='teamlogos']"))
            )
        for _ in range(3):
            time.sleep(2)
            html = driver.page_source
    except TimeoutException:
        html = driver.page_source
    finally:
        driver.quit()
    return BeautifulSoup(html, "html.parser")


def _extract_premiership_clubs(url: str) -> Tuple[List[str], Dict[str, dict]]:
    soup = _fetch_html(url)
    team_names: Set[str] = set()
    logos: Dict[str, dict] = {}
    blacklist = {
        "Gallagher",
        "PRL logo",
        "Partner Name",
        "logo",
        "App Store",
        "Google Play",
    }
    for img in soup.find_all("img", alt=True, src=True):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "")
        if not alt or alt in blacklist:
            continue
        if "media-cdn.incrowdsports.com" in src or "media-cdn.cortextech.io" in src:
            team_names.add(alt)
            logos[alt] = {"logo_url": src, "badge_url": src}
    return sorted(team_names), logos


def _extract_epcr_clubs(url: str) -> Tuple[List[str], Dict[str, dict]]:
    try:
        soup = _fetch_html(url)
    except Exception:
        soup = _fetch_html_selenium(url)
    logos: Dict[str, dict] = {}
    team_names: Set[str] = set()
    for name_el in soup.select("p.club-name"):
        name = (name_el.get_text(strip=True) or "").strip()
        if not name:
            continue
        team_names.add(name)
        img = name_el.find_parent().find("img", src=True)
        if img:
            src = (img.get("src") or "").strip()
            if src:
                logos[name] = {"logo_url": src, "badge_url": src}
    return sorted(team_names), logos


def _extract_top14_clubs(url: str) -> Tuple[List[str], Dict[str, dict]]:
    soup = _fetch_html(url)
    team_names: Set[str] = set()
    logos: Dict[str, dict] = {}
    for img in soup.find_all("img", alt=True, src=True):
        alt = (img.get("alt") or "").strip()
        src = (img.get("src") or "")
        if not alt:
            continue
        if "cdn.lnr.fr/club" in src:
            team_names.add(alt)
            logos[alt] = {"logo_url": src, "badge_url": src}
    return sorted(team_names), logos


def _extract_jrlo_division(url: str, division: str) -> Tuple[List[str], Dict[str, dict]]:
    soup = _fetch_html(url)
    teams: List[str] = []
    logos: Dict[str, dict] = {}
    if division == "1":
        base_names = LeagueOneDivisionsScraper.DIVISION_1_TEAMS
    elif division == "2":
        base_names = LeagueOneDivisionsScraper.DIVISION_2_TEAMS
    else:
        base_names = LeagueOneDivisionsScraper.DIVISION_3_TEAMS

    for section in soup.select("section.division"):
        text = " ".join(section.stripped_strings).upper()
        if f"DIVISION {division}" not in text and f"DIVISION{division}" not in text:
            continue
        for img in section.find_all("img", alt=True, src=True):
            src = img.get("src") or ""
            if "team_info" not in src:
                continue
            name = (img.get("alt") or "").strip()
            if name:
                # Normalize to base name if possible (to align with match data)
                mapped = None
                for base in base_names:
                    if base in name:
                        mapped = base
                        break
                final_name = mapped or name
                teams.append(final_name)
                if src:
                    if src.startswith("/"):
                        src = f"https://league-one.jp{src}"
                    logos[final_name] = {"logo_url": src, "badge_url": src}
    return sorted(dict.fromkeys(teams)), logos


def _extract_six_nations_teams(competition_id: str) -> Tuple[List[str], Dict[str, dict]]:
    if competition_id == "m6n":
        scraper = SixNationsScraper()
    elif competition_id == "w6n":
        scraper = SixNationsWomensScraper()
    else:
        scraper = SixNationsU20Scraper()

    try:
        scraper._initialize_driver_and_load_page()
        soup = BeautifulSoup(scraper.driver.page_source, "html.parser")
        scraper._extract_team_logos(soup)
        raw_names = list(scraper._team_logos_cache.keys())
        # Filter by known country codes/names to remove sponsor logos
        valid = set()
        logos: Dict[str, dict] = {}
        country_keys = {k.upper() for k in BaseScraper.COUNTRY_CODES.keys()}
        country_vals = {v.upper() for v in BaseScraper.COUNTRY_CODES.values()}
        for name in raw_names:
            key = name.strip().upper()
            if key in country_keys or key in country_vals:
                normalized = name.strip()
                valid.add(normalized)
                entry = scraper._team_logos_cache.get(name) or scraper._team_logos_cache.get(normalized)
                if isinstance(entry, dict):
                    logo_url = entry.get("logo_url", "")
                else:
                    logo_url = entry or ""
                if logo_url:
                    logos[normalized] = {"logo_url": logo_url, "badge_url": logo_url}
        return sorted(valid), logos
    finally:
        if scraper.driver:
            scraper.driver.quit()


def _extract_urc_clubs(url: str) -> Tuple[List[str], Dict[str, dict]]:
    soup = _fetch_html_selenium(url)
    logos: Dict[str, dict] = {}

    # Extract logos from page URLs (WordPress uploads contain team logos)
    urls = set()
    for link in soup.find_all(["a", "img"]):
        href = link.get("href") if link.name == "a" else None
        src = link.get("src") if link.name == "img" else None
        if href:
            urls.add(href)
        if src:
            urls.add(src)
    # Also scan raw HTML for asset URLs
    for match in re.findall(r"https?://[^\"\\s>]+", str(soup)):
        urls.add(match)

    urc_name_map = {
        "Benetton-Rugby": "Benetton Rugby",
        "Cardiff-Rugby": "Cardiff Rugby",
        "Connacht": "Connacht Rugby",
        "Dragons": "Dragons RFC",
        "Edinburgh": "Edinburgh Rugby",
        "Glasgow-Warriors": "Glasgow Warriors",
        "Hollywoodbets-Sharks": "Hollywoodbets Sharks",
        "Leinster": "Leinster Rugby",
        "Munster-Rugby": "Munster Rugby",
        "Ospreys": "Ospreys",
        "Scarlets": "Scarlets",
        "Ulster": "Ulster Rugby",
        "Zebre-Parma": "Zebre Parma",
        "Vodacom": "Vodacom Bulls",
        "Stormers": "DHL Stormers",
        "Stormers-Light": "DHL Stormers",
        "Lions-logo-dark-ver": "Lions",
        "Lions-White-Logo": "Lions",
    }

    for url in urls:
        if "wp-content/uploads" not in url:
            continue
        if url.endswith("&quot;);") or url.endswith("&quot;)"):
            url = url.split("&quot;")[0]
        if not (url.endswith(".svg") or url.endswith(".png") or url.endswith(".jpg") or url.endswith(".jpeg")):
            continue
        filename = url.split("/")[-1]
        if not filename:
            continue
        base = filename.replace(".svg", "").replace(".png", "").replace(".jpg", "").replace(".jpeg", "")
        base = base.replace("-1", "")
        if base not in urc_name_map:
            continue
        team_name = urc_name_map.get(base)
        if team_name:
            logos[team_name] = {"logo_url": url, "badge_url": url}

    team_names = sorted(logos.keys())
    return team_names, logos


def _extract_srp_teams(url: str) -> Tuple[List[str], Dict[str, dict]]:
    logos: Dict[str, dict] = {}
    teams: Set[str] = set()

    name_map = {
        "NSW Waratahs": "NSW Waratahs",
        "Queensland Reds": "Queensland Reds",
        "Western Force": "Western Force",
        "Force": "Western Force",
    }

    def parse_srp(soup: BeautifulSoup) -> None:
        for img in soup.find_all("img", alt=True, src=True):
            alt = (img.get("alt") or "").strip()
            src = (img.get("src") or "").strip()
            if "/teamlogos/" not in src:
                continue
            if src.startswith("/"):
                src = f"https://super.rugby{src}"
            team_name = name_map.get(alt, alt)
            if not team_name:
                continue
            teams.add(team_name)
            logos[team_name] = {"logo_url": src, "badge_url": src}

    soup = _fetch_html(url)
    parse_srp(soup)
    if not teams:
        soup = _fetch_html_selenium(url)
        parse_srp(soup)

    return sorted(teams), logos


def _extract_jrlo_short_names(url: str) -> Dict[str, str]:
    """Extract JRLO short names from official about page."""
    soup = _fetch_html(url)
    mapping: Dict[str, str] = {}
    invalid_values = {"略称", "公式チーム名称", "呼称", "エンブレム"}

    def _clean(value: str) -> str:
        return _normalize_short_name_width((value or "").strip())

    def _is_invalid(value: str) -> bool:
        return not value or value in invalid_values

    # Parse structured rows first (stable against header text noise).
    for row in soup.select("div.about-teams ul li"):
        row_values: Dict[str, str] = {}
        for dl in row.select("dl"):
            key_el = dl.find("dt")
            value_el = dl.find("dd")
            if not key_el or not value_el:
                continue
            key = (key_el.get_text(" ", strip=True) or "").strip()
            value = _clean(value_el.get_text(" ", strip=True))
            row_values[key] = value

        short_name = row_values.get("略称", "")
        official_name = row_values.get("公式チーム名称", "")
        call_name = row_values.get("呼称", "")
        img_alt = ""
        img = row.select_one("img[alt]")
        if img:
            img_alt = _clean(img.get("alt", ""))

        if _is_invalid(short_name):
            continue

        for candidate in (official_name, call_name, img_alt):
            if _is_invalid(candidate):
                continue
            mapping[candidate] = short_name

    return mapping


def _normalize_short_name_width(value: str) -> str:
    """Normalize ASCII width in short names (e.g., ＷＫ -> WK)."""
    import unicodedata

    if not value:
        return value
    return unicodedata.normalize("NFKC", value)


def _is_short_name_placeholder(value: str) -> bool:
    normalized = _normalize_short_name_width((value or "").strip())
    return normalized in {"", "略称", "公式チーム名称", "呼称", "エンブレム"}




def _collect_teams_for_comp(comp_id: str, cfg: dict) -> Tuple[List[str], Dict[str, dict]]:
    source_type = cfg.get("type")
    if source_type == "premiership-clubs":
        return _extract_premiership_clubs(cfg["url"])
    if source_type == "epcr-clubs":
        return _extract_epcr_clubs(cfg["url"])
    if source_type == "top14-clubs":
        return _extract_top14_clubs(cfg["url"])
    if source_type == "jrlo-teams":
        if comp_id.endswith("div1"):
            return _extract_jrlo_division(cfg["url"], "1")
        if comp_id.endswith("div2"):
            return _extract_jrlo_division(cfg["url"], "2")
        if comp_id.endswith("div3"):
            return _extract_jrlo_division(cfg["url"], "3")
        return [], {}
    if source_type == "six-nations-fixtures":
        return _extract_six_nations_teams(comp_id)
    if source_type == "urc-clubs":
        return _extract_urc_clubs(cfg["url"])
    if source_type == "srp-teams":
        return _extract_srp_teams(cfg["url"])

    return [], {}


def update_team_master(only: List[str] | None = None, fetch_logos: bool = True) -> None:
    sources = _load_sources()
    if only:
        sources = {k: v for k, v in sources.items() if k in only}

    teams_by_comp: Dict[str, List[str]] = {}
    logos_by_comp: Dict[str, Dict[str, dict]] = {}
    existing_teams = load_existing_teams()
    canonical_short_names = {
        team_id: (team_data.get("short_name") or "").strip()
        for team_id, team_data in existing_teams.items()
        if (team_data.get("short_name") or "").strip()
    }
    jrlo_short_names: Dict[str, str] = {}
    srp_aliases = {
        "BLUES": "Blues",
        "BRUMBIES": "Brumbies",
        "CHIEFS": "Chiefs",
        "CRUSADERS": "Crusaders",
        "FIJIAN DRUA": "Fijian Drua",
        "FORCE": "Western Force",
        "HIGHLANDERS": "Highlanders",
        "HURRICANES": "Hurricanes",
        "MOANA PASIFIKA": "Moana Pasifika",
        "REDS": "Queensland Reds",
        "WARATAHS": "NSW Waratahs",
    }
    for team_data in existing_teams.values():
        if team_data.get("competition_id") != "srp":
            continue
        name = (team_data.get("name") or "").strip()
        mapped = srp_aliases.get(name.upper())
        if mapped:
            team_data["name"] = mapped
            if not (team_data.get("short_name") or "").strip():
                team_data["short_name"] = mapped

    for comp_id, cfg in sources.items():
        if not comp_id.startswith("jrlo"):
            continue
        short_url = cfg.get("short_names_url")
        if short_url:
            try:
                jrlo_short_names = _extract_jrlo_short_names(short_url)
            except Exception as exc:  # noqa: BLE001
                print(f"  ⚠️ JRLO略称取得失敗: {exc}")
            break
    for comp_id, cfg in sources.items():
        print(f"\n大会: {comp_id}")
        try:
            teams, logos = _collect_teams_for_comp(comp_id, cfg)
            if not teams:
                print("  ⚠️ チーム取得結果が空です（ソース/セレクタ要確認）")
                fallback = [
                    t.get("name", "")
                    for t in existing_teams.values()
                    if t.get("competition_id") == comp_id and t.get("name")
                ]
                if fallback:
                    teams = sorted(set(fallback))
                    print(f"  ↩️ 既存マスタから復元: {len(teams)}チーム")
            teams_by_comp[comp_id] = teams
            logos_by_comp[comp_id] = logos or {}
            print(f"  {comp_id}: {len(teams)}チーム")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠️ エラー: {exc}")
            fallback = [
                t.get("name", "")
                for t in existing_teams.values()
                if t.get("competition_id") == comp_id and t.get("name")
            ]
            if fallback:
                teams = sorted(set(fallback))
                print(f"  ↩️ 既存マスタから復元: {len(teams)}チーム")
                teams_by_comp[comp_id] = teams
                logos_by_comp[comp_id] = {}
            else:
                teams_by_comp[comp_id] = []
                logos_by_comp[comp_id] = {}

    new_teams, added_count, preserved_count = generate_team_master(
        teams_by_comp,
        existing_teams,
        fetch_logos=False,
        official_logos_by_comp=logos_by_comp if fetch_logos else None,
    )

    if only:
        preserved = {
            team_id: team_data
            for team_id, team_data in existing_teams.items()
            if team_data.get("competition_id") not in only
        }
        merged_teams = {**preserved, **new_teams}
    else:
        merged_teams = new_teams

    if jrlo_short_names:
        for team_data in merged_teams.values():
            comp_id = team_data.get("competition_id", "")
            if not comp_id.startswith("jrlo"):
                continue
            official_name = team_data.get("name", "").strip()
            short_name = jrlo_short_names.get(official_name)
            current_short_name = (team_data.get("short_name") or "").strip()
            if not short_name:
                continue
            normalized_short_name = _normalize_short_name_width(short_name)
            if (
                not current_short_name
                or _is_short_name_placeholder(current_short_name)
                or current_short_name == official_name
            ):
                team_data["short_name"] = normalized_short_name

    # Preserve canonical short_name from the pre-update master.
    if canonical_short_names:
        for team_id, team_data in merged_teams.items():
            canonical = canonical_short_names.get(team_id)
            if not canonical or _is_short_name_placeholder(canonical):
                continue

            comp_id = team_data.get("competition_id", "")
            team_name = (team_data.get("name") or "").strip()
            if comp_id.startswith("jrlo") and jrlo_short_names:
                target = jrlo_short_names.get(team_name)
                if target:
                    normalized_target = _normalize_short_name_width(target)
                    normalized_canonical = _normalize_short_name_width(canonical)
                    if normalized_target != normalized_canonical:
                        continue

            if team_data.get("short_name") != canonical:
                team_data["short_name"] = canonical

    with TEAMS_JSON.open("w", encoding="utf-8") as f:
        json.dump(merged_teams, f, ensure_ascii=False, indent=2)
        f.write("\n")

    duplicates = detect_duplicates(teams_by_comp)
    if duplicates:
        print("\n⚠️ 重複候補:")
        for dup in duplicates[:10]:
            print(f"  - {dup['competition_id']}: {', '.join(dup['variations'])}")

    print("\n✅ teams.json 更新完了")
    print(f"総チーム数: {len(merged_teams)}")
    print(f"  - 既存ID保持: {preserved_count}")
    print(f"  - 新規追加: {added_count}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Update teams.json from official team list sources.")
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated competition IDs to update (e.g., premier,urc,m6n).",
    )
    parser.add_argument(
        "--no-logos",
        action="store_true",
        help="Skip logo fetch during team master update.",
    )
    args = parser.parse_args(argv)

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    update_team_master(only, fetch_logos=not args.no_logos)


if __name__ == "__main__":
    main()
