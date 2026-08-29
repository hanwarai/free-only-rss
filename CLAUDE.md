# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Scrapes the series listing page of 8 Japanese web-manga publishers, then emits a single Atom feed (`feeds/rss.xml`) where each entry's `link` is that series' per-series RSS URL with `?free_only=1` appended. Also renders `feeds/index.html` (Jinja2 + Bootstrap) listing all series with "/feed subscribe" copy-to-clipboard buttons. The output directory `feeds/` is published to GitHub Pages by `.github/workflows/gh-pages.yaml` on push to `main` and on a 12-hour cron.

The publishers covered are hard-coded in `main.py` as one `parse_*` function each, listed in the `PUBLISHERS` tuple:

| Publisher | Parser | Series page | Item selector | series_id source |
|---|---|---|---|---|
| COMIC DAYS | `parse_comic_days` | `/series` | `li.daily-series-item` | `data-series-id` attr |
| 少年ジャンプ＋ | `parse_shonenjumpplus` | `/series` | `li.series-list-item` | parsed from `img[data-src]` URL |
| サンデーうぇぶり | `parse_sunday_webry` | `/series` | `li.webry-series-item` | parsed from `img[data-src]` URL |
| となりのヤングジャンプ | `parse_tonarinoyj` | `/series` | `li.subpage-table-list-item` | `id="series-..."` |
| くらげバンチ | `parse_kuragebunch` | `/series/kuragebunch` | `li.page-series-list-item` | parsed from `img[data-src]` URL |
| コミックガルド | `parse_comic_gardo` | `/series` | `li` whose only class matches `^s\d+$` | that same class token, strip `s` prefix |
| Webアクション | `parse_comic_action` | `/series` | `li[class^="SeriesListItem_item__"]` | parsed from `img[src]` URL |
| コミック アース・スター | `parse_comic_earthstar` | `/series` | `ul[class^="SeriesList_series_list__"] li` | parsed from `img[src]` URL |

Sites that use hashed CSS module class names (Webアクション, コミック アース・スター) require prefix matching (`re.compile('^...')` / `[class^=...]`) — these classes change between deploys of the upstream site, so a hardcoded full class name will break silently. The two URL-shape variants (`%2F`-encoded vs raw `/`) reflect what each upstream actually emits; do not "normalize" them.

コミックガルド went the same way but its `li` carries no `SeriesListItem_*` class at all — the hashed classes sit on the children, and the `li`'s only class is `s{series_id}`. That token is derived from the series id rather than from a build hash, so it is the one stable anchor on the page; match the `li` on `^s\d+$` rather than on anything hashed.

## Commands

Python 3.13, managed by `uv` (lockfile `uv.lock`):

```bash
uv sync --all-extras # install deps (including the dev extra) from uv.lock
uv run main.py       # scrape all 8 sites and write feeds/rss.xml + feeds/index.html
SSL_VERIFY=False uv run main.py   # disable TLS verification (debugging only)
uv run pytest        # tests; fails under 80% coverage of main.py
uv run ruff check .  # lint
uv run ruff format . # format
uv run mypy          # type check
uv run pre-commit install   # run ruff + mypy on every commit
```

Two workflows:

- `.github/workflows/ci.yaml` runs on `pull_request` — lint, format check, mypy, pytest. It deliberately does **not** run `uv run main.py`: hitting all 8 upstream sites would make a PR's mergeability depend on their availability.
- `.github/workflows/gh-pages.yaml` runs the real scrape on `push` to `main` and on the 12-hour cron, then publishes `feeds/` to Pages. It also runs on `pull_request` with the artifact upload and the `publish` job skipped, so a PR never touches Pages.

Both resolve the pinned uv version through `.github/scripts/resolve-uv-version.sh` so the two workflows cannot drift; `tests/test_resolve_uv_version.py` pins that script's contract.

## Architecture Notes

- `main.py` keeps one `parse_*` function per publisher, each taking the page HTML and returning `list[Series]`. When a publisher's HTML changes, only its function needs editing. Do **not** collapse the eight into a selector table driving one generic scraper: the per-publisher differences (`%2F`-encoded vs raw `/`, attribute vs class-token ids) are the thing that has to stay visible and separately testable.
- The pipeline is `collect()` → `build_feed()` → `report()` → `write_outputs()`, wired by `main()`. Everything except `fetch()` is pure, which is what makes the fixture tests possible.
- `scrape()` returns three distinguishable states: a non-empty list, an empty list (selector matched nothing), and `None` (fetch or parse raised). `report()` maps them to different messages, so keep them distinct — collapsing empty into `None` would send you hunting for a network problem when a selector broke.
- `fetch()` calls `raise_for_status()` on purpose: an upstream error page parsed as HTML yields zero hits and would otherwise be misdiagnosed as a broken selector.
- A publisher whose parse raises is dropped whole rather than published half-scraped — `build_feed()` skips `None` results entirely.
- All entries are added to a single `feedgenerator.Atom1Feed` with a constant `updateddate` of `2025-01-01`. This is intentional: the feed exists to advertise per-series subscription URLs, not to signal "new" series — readers should not re-fetch entries on date changes.
- `feeds/.gitkeep` is the only checked-in file under `feeds/`. The generated `rss.xml` and `index.html` are never committed; they live only as the Pages artifact.
- `_dedupe()` is required because some series pages render the same series in multiple sections (e.g. recommended + alphabetical).
- `report()` prints a per-publisher series count and emits a `[WARN]` (plus a GitHub Actions `::warning::` annotation under CI) for any publisher that yielded nothing, and `emit_github_output()` puts the same list on the step's `problems` output for the workflow to act on. `scrape()` only swallows exceptions, so a selector that stops matching produces zero items and no error — コミックガルド silently dropped out of the feed that way. The run deliberately still exits 0 so a single broken publisher does not block publishing the other seven; that also means `failure()`-conditioned notifications cannot see this case, hence the separate `problems` output.
- `tests/fixtures/*.html` are real excerpts (3 matching elements each) cut from the live listing pages, and `tests/fixtures/expected.json` is the snapshot read from them. Hand-written HTML would not catch the one failure mode this project actually has: upstream quietly changing its markup.

## When Adding a New Publisher

1. Add a `parse_*` function to `main.py` matching the existing pattern, and append a `Publisher(...)` entry to `PUBLISHERS`. Nothing else needs touching — the Atom feed and the HTML index are both driven off `PUBLISHERS`.
2. Verify the per-series RSS URL shape on that publisher's site — most use `/rss/series/{id}?free_only=1` but confirm; the `?free_only=1` query is the whole point of this project.
3. Cut a fixture: fetch the listing page, keep the first 3 matching elements (plus the wrapper element if the selector needs one), save as `tests/fixtures/{name}.html`, and add the expected `[series_id, title]` pairs to `tests/fixtures/expected.json`.
4. Add the parser to the `PARSERS` table in `tests/test_parsers.py`. `test_every_publisher_has_a_parser_test` fails if you forget.
