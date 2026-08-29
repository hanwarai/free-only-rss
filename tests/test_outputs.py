"""生成物の書き出し。"""

from pathlib import Path

import main

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_writes_feed_and_index_creating_the_directory(tmp_path: Path) -> None:
    rss, sites = main.build_feed(
        [
            (
                main.Publisher(
                    "COMIC DAYS", "https://d.test/series", "https://d.test", lambda h: []
                ),
                [main.Series("1", "テスト作品")],
            )
        ]
    )
    output = tmp_path / "feeds"
    main.write_outputs(rss, sites, output, REPO_ROOT / "templates")

    feed = (output / "rss.xml").read_text(encoding="utf-8")
    index = (output / "index.html").read_text(encoding="utf-8")
    assert "https://d.test/rss/series/1?free_only=1" in feed
    assert "テスト作品" in index
    assert "/feed subscribe https://d.test/rss/series/1?free_only=1" in index


def test_index_escapes_series_titles(tmp_path: Path) -> None:
    rss, sites = main.build_feed(
        [
            (
                main.Publisher(
                    "COMIC DAYS", "https://d.test/series", "https://d.test", lambda h: []
                ),
                [main.Series("1", "<script>x</script>")],
            )
        ]
    )
    main.write_outputs(rss, sites, tmp_path / "feeds", REPO_ROOT / "templates")
    index = (tmp_path / "feeds" / "index.html").read_text(encoding="utf-8")
    assert "<script>x</script>" not in index
    assert "&lt;script&gt;" in index
