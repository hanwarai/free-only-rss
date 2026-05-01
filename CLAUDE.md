# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Scrapes the series listing page of 8 Japanese web-manga publishers, then emits a single Atom feed (`feeds/rss.xml`) where each entry's `link` is that series' per-series RSS URL with `?free_only=1` appended. Also renders `feeds/index.html` (Jinja2 + Bootstrap) listing all series with "/feed subscribe" copy-to-clipboard buttons. The output directory `feeds/` is published to GitHub Pages by `.github/workflows/gh-pages.yaml` on push to `main` and on a 12-hour cron.

The publishers covered (and their selectors) are hard-coded as repeated blocks in `main.py`:

| Publisher | Series page | Item selector | series_id source |
|---|---|---|---|
| COMIC DAYS | `/series` | `li.daily-series-item` | `data-series-id` attr |
| 少年ジャンプ＋ | `/series` | `li.series-list-item` | parsed from `img[data-src]` URL |
| サンデーうぇぶり | `/series` | `li.webry-series-item` | parsed from `img[data-src]` URL |
| となりのヤングジャンプ | `/series` | `li.subpage-table-list-item` | `id="series-..."` |
| くらげバンチ | `/series/kuragebunch` | `li.page-series-list-item` | parsed from `img[data-src]` URL |
| コミックガルド | `/series` | `li.series-section-item` | last class token, strip `s` prefix |
| Webアクション | `/series` | `li[class^="SeriesListItem_item__"]` | parsed from `img[src]` URL |
| コミック アース・スター | `/series` | `ul[class^="SeriesList_series_list__"] li` | parsed from `img[src]` URL |

Sites that use hashed CSS module class names (Webアクション, コミック アース・スター) require prefix matching (`re.compile('^...')` / `[class^=...]`) — these classes change between deploys of the upstream site, so a hardcoded full class name will break silently. The two URL-shape variants (`%2F`-encoded vs raw `/`) reflect what each upstream actually emits; do not "normalize" them.

## Commands

Python 3.13, managed by `uv` (lockfile `uv.lock`):

```bash
uv sync              # install deps from uv.lock
uv run main.py       # scrape all 8 sites and write feeds/rss.xml + feeds/index.html
SSL_VERIFY=False uv run main.py   # disable TLS verification (debugging only)
```

There are no tests, linters, or formatters configured. CI runs only `uv run main.py` and uploads `feeds/` as a Pages artifact.

## Architecture Notes

- `main.py` is a flat top-to-bottom script — one block per publisher with the same scrape-and-emit pattern. When a publisher's HTML changes, only its block needs editing.
- All entries are added to a single `feedgenerator.Atom1Feed` with a constant `updateddate` of `2025-01-01`. This is intentional: the feed exists to advertise per-series subscription URLs, not to signal "new" series — readers should not re-fetch entries on date changes.
- `feeds/.gitkeep` is the only checked-in file under `feeds/`. The generated `rss.xml` and `index.html` are never committed; they live only as the Pages artifact.
- `unique_ids` per-block dedupe is required because some series pages render the same series in multiple sections (e.g. recommended + alphabetical).

## When Adding a New Publisher

1. Append a new block to `main.py` matching the existing pattern.
2. Verify the per-series RSS URL shape on that publisher's site — most use `/rss/series/{id}?free_only=1` but confirm; the `?free_only=1` query is the whole point of this project.
3. The block must populate both `rss.add_item(...)` and `feeds.append({title, url})`, then `sites.append({title, feeds})` so both the Atom feed and the HTML index get the entries.
