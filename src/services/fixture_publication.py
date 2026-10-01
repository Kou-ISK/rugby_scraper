"""Validation and atomic publication shared by the runner and manifest builder.

Only freshly collected, validated file hashes are trusted. Old files remain on
disk (and in Git history), but their plausible-looking dates are not promoted.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VALIDATION_VERSION = 2


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_instant(value):
    if not value or not isinstance(value, str):
        raise ValueError("Kickoff is missing or is not an ISO string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Kickoff has no timezone offset")
    if not 2000 <= dt.year <= 2100:
        raise ValueError("Kickoff year is outside the supported range")
    return dt.astimezone(timezone.utc)


def validate_match_file(path, competition_id=None):
    path = Path(path)
    competition_id = competition_id or path.parent.name
    matches = load_json(path)
    if not isinstance(matches, list) or not matches:
        raise ValueError("Fixture file must be a nonempty array; preserve previous data for an empty result")
    ids = set()
    stable_ids = set()
    dates = []
    unknown = 0
    for index, match in enumerate(matches):
        prefix = f"{path.name} row {index}"
        if not isinstance(match, dict):
            raise ValueError(f"{prefix}: match must be an object")
        for key in ("match_id", "stable_id", "competition_id", "season", "home_team", "away_team"):
            if not isinstance(match.get(key), str) or not match[key].strip():
                raise ValueError(f"{prefix}: {key} must be a nonempty string")
        if match["competition_id"] != competition_id or match["season"] != path.stem:
            raise ValueError(f"{prefix}: competition/season does not match its actual path")
        if match["match_id"] in ids or match["stable_id"] in stable_ids:
            raise ValueError(f"{prefix}: duplicate match identity")
        ids.add(match["match_id"])
        stable_ids.add(match["stable_id"])
        if match.get("identity_strength") not in ("official", "url", "weak"):
            raise ValueError(f"{prefix}: identity strength is missing")
        if not isinstance(match.get("broadcasters"), list):
            raise ValueError(f"{prefix}: broadcasters must be an array")
        local, utc = match.get("kickoff"), match.get("kickoff_utc")
        if bool(local) != bool(utc):
            raise ValueError(f"{prefix}: local and UTC kickoffs must both be known or unknown")
        if not utc:
            unknown += 1
            continue
        local_instant, utc_instant = parse_instant(local), parse_instant(utc)
        if local_instant != utc_instant:
            raise ValueError(f"{prefix}: local and UTC kickoffs disagree")
        if not str(utc).endswith("Z"):
            raise ValueError(f"{prefix}: kickoff_utc must use the UTC Z suffix")
        tz_name = match.get("timezone") or ""
        try:
            tz = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError):
            # Some official APIs expose only an explicit venue offset.
            if tz_name != "UTC" and not __import__("re").fullmatch(r"(?:UTC)?[+-]\d{2}:\d{2}", tz_name):
                raise ValueError(f"{prefix}: invalid source timezone")
        else:
            given = datetime.fromisoformat(local.replace("Z", "+00:00"))
            if given.utcoffset() != local_instant.astimezone(tz).utcoffset():
                raise ValueError(f"{prefix}: kickoff offset disagrees with IANA timezone")
        dates.append(utc_instant.isoformat().replace("+00:00", "Z"))
    if not dates:
        raise ValueError("No usable kickoffs were collected; preserve the last known good file")
    return {
        "match_count": len(matches),
        "known_kickoffs": len(dates),
        "unknown_kickoffs": unknown,
        "date_range": {"start": min(dates), "end": max(dates)},
    }


def is_verified_file(path, health, data_dir):
    relative = "data/" + Path(path).relative_to(data_dir).as_posix()
    record = health.get("files", {}).get(relative, {})
    return (record.get("validation_version") == VALIDATION_VERSION
            and record.get("sha256") == file_sha256(path))
