"""TheSportsDB から大会・チームのロゴURLを取得し、JSONに反映するスクリプト。

使い方:
  python scripts/fetch_logos.py --config scripts/logo_sources.json --save-local

設定ファイルフォーマット例 (scripts/logo_sources.json):
{
  "competitions": [
    {
      "id": "six-nations",
      "league_id": "1234",
      "league_name": "Six Nations",
      "license_key": "six_nations_logo",
      "save_competition_logo_to_repo": false,
      "save_team_logos_to_repo": false,
      "team_license_key": null,
      "team_slug_overrides": {"Ireland": "ireland"}
    }
  ],
  "license_entries": {
    "six_nations_logo": {
      "license": "external_only",
      "source": "TheSportsDB",
      "notes": "外部URLのみ参照"
    }
  }
}

注意:
- オリジナルURLが利用できる場合は logo_url/badge_url を優先し、ライセンス的に再配布できる場合のみ --save-local でリポジトリ保存。
- S3等にアップロードしたい場合は、このスクリプトでダウンロード後に別途 upload_to_s3.py などを呼び出してください。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
ASSETS_DIR = ROOT / "assets" / "logos"
COMPETITIONS_JSON = DATA_DIR / "competitions.json"
TEAM_LOGOS_JSON = DATA_DIR / "team_logos.json"
TEAMS_JSON = DATA_DIR / "teams.json"
LICENSES_JSON = DATA_DIR / "logo_licenses.json"

DEFAULT_API_KEY = os.environ.get("THESPORTSDB_API_KEY", "123")
API_BASE = "https://www.thesportsdb.com/api/v1/json"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fetch_json(url: str) -> Dict[str, Any]:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content))


def save_image(img: Image.Image, dest: Path, max_width: int) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    img.save(dest)
    return dest


def update_competition_logo(
    competitions: List[Dict[str, Any]],
    comp_cfg: Dict[str, Any],
    allow_repo_save: bool,
    max_width: int,
) -> Optional[str]:
    comp_id = comp_cfg["id"]
    league_id = comp_cfg["league_id"]
    url = f"{API_BASE}/{DEFAULT_API_KEY}/lookupleague.php?id={league_id}"
    payload = fetch_json(url)
    leagues = payload.get("leagues") or []
    if not leagues:
        print(f"[warn] league not found: {comp_id} (id={league_id})")
        return None

    logo_url = leagues[0].get("strLogo")
    if not logo_url:
        print(f"[info] no logo_url for {comp_id}")

    repo_path: Optional[str] = None
    if allow_repo_save and comp_cfg.get("save_competition_logo_to_repo") and logo_url:
        try:
            img = download_image(logo_url)
            dest = ASSETS_DIR / "competitions" / f"{comp_id}.png"
            save_image(img, dest, max_width)
            repo_path = str(dest.relative_to(ROOT).as_posix())
            print(f"[info] saved competition logo -> {repo_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] failed to save competition logo for {comp_id}: {exc}")

    for comp in competitions:
        if comp.get("id") != comp_id:
            continue
        if logo_url:
            comp["logo_url"] = logo_url
        if repo_path:
            comp["logo_repo_path"] = repo_path
            comp["logo_url"] = ""
        if comp_cfg.get("license_key"):
            comp["license_key"] = comp_cfg["license_key"]
        break
    else:
        print(f"[warn] competition id not in competitions.json: {comp_id}")

    return logo_url


def update_team_logos(
    comp_cfg: Dict[str, Any],
    allow_repo_save: bool,
    max_width: int,
    team_logos: Dict[str, List[Dict[str, Any]]],
    team_master: Dict[str, Any],
) -> None:
    comp_id = comp_cfg["id"]
    league_name = comp_cfg["league_name"]
    url = f"{API_BASE}/{DEFAULT_API_KEY}/search_all_teams.php?l={quote_plus(league_name)}"
    payload = fetch_json(url)
    teams = payload.get("teams") or []
    if not teams:
        print(f"[warn] no teams found for {comp_id} ({league_name})")
        return

    existing: Dict[str, Dict[str, Any]] = {
        entry.get("team", slugify(entry.get("team", ""))): entry
        for entry in team_logos.get(comp_id, [])
    }

    overrides = comp_cfg.get("team_slug_overrides", {})
    save_team_repo = allow_repo_save and comp_cfg.get("save_team_logos_to_repo", False)
    team_license_key = comp_cfg.get("team_license_key")

    updated_entries: List[Dict[str, Any]] = []
    for team in teams:
        team_name = team.get("strTeam") or ""
        slug = overrides.get(team_name) or slugify(team_name)
        master_key = slug.lower()

        if master_key in team_master:
            # prefer master key as id/slug to keep consistency
            slug = master_key
        badge_url = team.get("strBadge")
        logo_url = team.get("strLogo")

        entry = existing.get(slug, {"team": slug})
        if badge_url:
            entry["badge_url"] = badge_url
        if logo_url:
            entry["logo_url"] = logo_url
        if team_license_key:
            entry["license_key"] = team_license_key

        repo_path: Optional[str] = entry.get("logo_repo_path")
        if save_team_repo and badge_url:
            try:
                img = download_image(badge_url)
                dest = ASSETS_DIR / "teams" / f"{slug}.png"
                save_image(img, dest, max_width)
                repo_path = str(dest.relative_to(ROOT).as_posix())
                entry["logo_repo_path"] = repo_path
                entry["badge_url"] = ""
                print(f"[info] saved team badge -> {repo_path}")
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] failed to save badge for {team_name}: {exc}")

        updated_entries.append(entry)

    team_logos[comp_id] = sorted(updated_entries, key=lambda e: e.get("team", ""))


def merge_license_entries(config: Dict[str, Any], license_book: Dict[str, Any]) -> None:
    for key, value in (config.get("license_entries") or {}).items():
        license_book[key] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch logos from TheSportsDB and update JSON metadata.")
    parser.add_argument("--config", default="scripts/logo_sources.json", help="Path to config JSON")
    parser.add_argument("--only", nargs="*", help="Process only these competition ids")
    parser.add_argument("--save-local", action="store_true", help="Download images into assets/logos")
    parser.add_argument("--resize-max-width", type=int, default=300, help="Max width when saving images")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_json(config_path, default=None)
    if config is None:
        raise SystemExit(
            f"Config file not found: {config_path}. Please create it using the format shown in fetch_logos.py docstring."
        )

    competitions_cfg = config.get("competitions") or []
    if args.only:
        only_set = set(args.only)
        competitions_cfg = [c for c in competitions_cfg if c.get("id") in only_set]

    competitions = load_json(COMPETITIONS_JSON, default=[])
    team_logos = load_json(TEAM_LOGOS_JSON, default={})
    team_master = load_json(TEAMS_JSON, default={})
    license_book = load_json(LICENSES_JSON, default={})

    for comp_cfg in competitions_cfg:
        update_competition_logo(competitions, comp_cfg, args.save_local, args.resize_max_width)
        update_team_logos(comp_cfg, args.save_local, args.resize_max_width, team_logos, team_master)

    merge_license_entries(config, license_book)

    if args.dry_run:
        print("[dry-run] No files were written.")
        return

    write_json(COMPETITIONS_JSON, competitions)
    write_json(TEAM_LOGOS_JSON, team_logos)
    write_json(LICENSES_JSON, license_book)
    print("[done] competitions.json, team_logos.json, logo_licenses.json updated")


if __name__ == "__main__":
    main()
