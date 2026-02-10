import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TEAMS_JSON = ROOT / "data" / "teams.json"

EXPECTED_COUNTS = {
    "premier": 10,
    "urc": 16,
    "epcr-champions": 24,
    "epcr-challenge": 18,
    "t14": 14,
    "m6n": 6,
    "w6n": 6,
    "u6n": 6,
    "jrlo-div1": 12,
    "jrlo-div2": 8,
    "jrlo-div3": 6,
    "srp": 11,
}

ALLOWED_DOMAINS = {
    "premier": {"media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "urc": {"www.unitedrugby.com", "unitedrugby.com"},
    "epcr-champions": {"www.epcrugby.com", "epcrugby.com", "media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "epcr-challenge": {"www.epcrugby.com", "epcrugby.com", "media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "t14": {"cdn.lnr.fr"},
    "m6n": {"www.sixnationsrugby.com", "sixnationsrugby.com", "contentfulproxy.stadion.io", "media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "w6n": {"www.sixnationsrugby.com", "sixnationsrugby.com", "contentfulproxy.stadion.io", "media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "u6n": {"www.sixnationsrugby.com", "sixnationsrugby.com", "contentfulproxy.stadion.io", "media-cdn.incrowdsports.com", "media-cdn.cortextech.io"},
    "jrlo-div1": {"league-one.jp", "www.league-one.jp", "league-one.s3.ap-northeast-1.amazonaws.com"},
    "jrlo-div2": {"league-one.jp", "www.league-one.jp", "league-one.s3.ap-northeast-1.amazonaws.com"},
    "jrlo-div3": {"league-one.jp", "www.league-one.jp", "league-one.s3.ap-northeast-1.amazonaws.com"},
    "srp": {"www.super.rugby", "super.rugby"},
}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def main() -> int:
    if not TEAMS_JSON.exists():
        print(f"teams.json not found: {TEAMS_JSON}")
        return 1

    with TEAMS_JSON.open("r", encoding="utf-8") as f:
        teams = json.load(f)

    by_comp = {}
    for team in teams.values():
        comp = team.get("competition_id")
        if not comp:
            continue
        by_comp.setdefault(comp, []).append(team)

    errors = 0

    for comp, expected in EXPECTED_COUNTS.items():
        comp_teams = by_comp.get(comp, [])
        actual = len(comp_teams)
        if actual != expected:
            print(f"[COUNT] {comp}: expected {expected}, got {actual}")
            errors += 1
        allowed = ALLOWED_DOMAINS.get(comp, set())
        for team in comp_teams:
            logo = team.get("logo_url") or ""
            if not logo:
                print(f"[MISSING] {comp}: {team.get('name')}")
                errors += 1
                continue
            domain = _domain(logo)
            if allowed and domain not in allowed:
                print(f"[DOMAIN] {comp}: {team.get('name')} -> {domain}")
                errors += 1

    if errors == 0:
        print("OK: All official logos validated.")
        return 0

    print(f"FAILED: {errors} issue(s) found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
