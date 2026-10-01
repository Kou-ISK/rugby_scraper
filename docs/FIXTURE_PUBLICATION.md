# Verified fixture publication

The authoritative index is `data/manifest.json` on the **data** branch:

```
https://raw.githubusercontent.com/Kou-ISK/rugby_scraper/data/data/manifest.json
```

Consumers fetch only `competitions[].data_paths`. These are existing JSON files
that were collected with the corrected parser, passed validation, and still match
their recorded SHA-256. Consumers must check the UTF-8 response bytes against the
corresponding `files[].sha256` before displaying matches. Fetch the manifest and
files at the same Git commit when possible. A concurrent data update can otherwise
cause a hash mismatch; retry the manifest instead of accepting mismatched data.

## Schema version 1

JRLO's official schedule may mix dated fixtures with cards explicitly marked
`日付未定`. Dated fixtures remain in verified match files; date-unannounced
cards are retained in `competitions[].collection_coverage.date_unannounced`
with stable identity, teams, venue, source URL and `date_not_announced` reason.
`observed_match_count`, `included_match_count` and `date_unannounced_count`
make the exclusion visible. This is coverage for the latest collection attempt,
separate from the verified file coverage and its last-success time.
The source-health ledger retains the same coverage. Unknown calendar dates do
not become midnight or a fabricated fixture date. If every card is date-unannounced,
the attempt is `no_fixtures` and retains previous data; malformed dates or clocks
still fail the source. Nested weekday spans are separated before strict date parsing.

The root contains `schema_version: 1`, `generated_at` (UTC ISO), and a
`competitions` array. Each competition contains:

| Field | Meaning |
| --- | --- |
| `id`, `name` | Existing competition identity/name |
| `data_paths` | Validated, real files relative to the repository root |
| `seasons` | Exact file stems, not years guessed from individual match dates |
| `status` | `healthy`, `partial`, `stale`, or `unavailable` |
| `last_success_at` | Last validated collection for this source, not a checkout mtime |
| `last_attempt_at`, `error` | Current source attempt and diagnostic |
| `coverage` | Counts/range for the verified files in `data_paths` only |
| `files` | All actual seasonal files, including retained/unverified files |

Each file has `path`, `season`, `sha256`, `match_count`, `known_kickoffs`,
`unknown_kickoffs`, `trust`, `validated_at`, and `error`. `trust: verified` means
the corrected collector and validation accepted that content. It does not mean
the organizer cannot reschedule a match or that broadcasting rights are final.
Unknown times remain unknown. They are excluded from calendar/timeline placement.

A nonempty all-unknown file can be verified when every record has a valid
calendar date, teams, venue, an explicit `kickoff_unknown_reason: not_announced`,
and an HTTPS official evidence URL whose host appears in the competition's
official sites/feeds. Unknown UTC coverage stays empty. `parse_failure` and
`not_available` are distinct from an official unannounced kickoff and cannot
justify all-unknown publication. Empty/invalid collection still keeps last-good.

Validation version 3 requires strict ISO kickoff strings, valid clock/calendar
fields, offsets with hours 00-23 and minutes 00-59, identical local/UTC instants,
and an exact match between the kickoff offset and its IANA or fixed source timezone.
An optional unknown-kickoff date must be a real YYYY-MM-DD calendar date. The
consumer and producer run the same `tests/fixtures/datetime-contract.json`
negative/positive cases. Invalid records reject staged publication and preserve
the verified last-good file. A hash-matching version2 last-good file is retained
only if it also passes the current validator. Other old/unverified files require
recollection; invalid old records never become verified through metadata alone.

`coverage.date_range` contains UTC `start`/`end` or empty strings when unavailable.
Counts obey `known_kickoffs + unknown_kickoffs = match_count`. The same verified
paths and dynamic summary are written to `competitions.json` and
`competitions_summary.json`. Static master fields, including logos and coverage
information, are preserved.

Old data predating this contract is retained, but it cannot be promoted merely by
running metadata generation: some old ISO dates have their month/day reversed.
Such files must be re-collected from their official source with the corrected code.

## Failure behavior

The runner copies each source into an isolated staging directory. A nonzero
process exit, timeout, invalid JSON, mismatched season/path, duplicate identity,
inconsistent local/UTC time, or severe drop in known fixtures rejects that source's
candidate files. Previous published files and validation hashes remain unchanged.
Healthy sources can still update. Empty responses retain existing files and report
`no_fixtures`; they do not silently clear history or claim a fresh successful fetch.

Sources that fail after a verified result become `stale`. Missing verified data is
`unavailable`. Unknown kickoffs or retained unverified seasonal files make the
available source `partial`. A verified source also becomes stale after 14 days
without a validated collection.

The weekly workflow publishes accepted data before reporting source failures to
CI. Draft branch dispatches upload evidence and do not publish to `data`. It does
not enable disabled schedules. The publisher uses a normal push and rejects a
concurrent data writer instead of force-overwriting its history.

## Commands

```bash
python scripts/automation/scrape_all.py
python scripts/automation/scrape_all.py --competition urc
python -m src.main generate-metadata
python scripts/automation/scrape_all.py --check-report
python -m unittest discover -s tests -v
```

Direct `python -m src.main urc` remains available for collector development, but
does not update the verified-publication ledger. Use the transactional runner for
published data. Local fake-run unit tests are not evidence of a real source fetch.

JRLO's essential schedule makes no print-detail HTTP requests by default. It
reuses known optional statistics by official match URL. Collector development can
opt into `python -m src.main jrlo --enrich-details`; secondary requests are limited
to recent finished matches, eight requests, and a 45-second enrichment budget.
An optional-stat failure cannot remove known fixture times or existing statistics.

## Saved plan identity

The old `match_id` is retained for consumer compatibility, but its sequence can
change after an earlier match is inserted. Identity version 2 generates
`stable_id` from **source provider + competition + season + official source ID**
(`source_match_id`), then a canonical match-specific official URL. IDs that an
organizer reuses in another season are distinct. `source_provider` and
`identity_version: 2` are explicit fields. Generic fixture/competition landing
pages never identify a single match. Within a season the identity is independent
of ordering and, with an official ID, kickoff changes. `identity_strength: weak`
signals a fallback for sources such as PDFs with no official ID/URL; saved plans
must retain their original snapshots and require an explicit user choice when a
refresh cannot be reconciled unambiguously.

When an older stable ID is upgraded, `previous_stable_ids` retains migration
candidates. Such an alias must never reconcile a saved plan on its own: confirm
its competition, season, provider/source identity or original official match URL
and snapshot as well. Old IDs could collide across seasons.

Dates with no kickoff time use `kickoff_date: YYYY-MM-DD` and empty `kickoff` /
`kickoff_utc`. They must never be turned into a synthetic midnight kickoff.

The NC collector/template and JRLO optional-stat cache are based on the existing
`agent/nations-championship` branch. Its unverified match data, old date parser,
and unbounded secondary-fetch behavior are not copied into publication.
