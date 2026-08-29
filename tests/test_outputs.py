"""生成物の書き出しと、ワークフローへの受け渡し。"""

import os
from pathlib import Path

import pytest

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


def test_emit_github_output_appends_problem_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "github_output"
    output.write_text("existing=1\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    main.emit_github_output(["コミックガルド", "Webアクション"])
    written = output.read_text(encoding="utf-8")
    assert written == "existing=1\nproblems=コミックガルド,Webアクション\n"


def test_emit_github_output_writes_an_empty_value_when_healthy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ワークフロー側が「キーが無い」と「問題なし」を区別しなくて済むようにする。"""
    output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    main.emit_github_output([])
    assert output.read_text(encoding="utf-8") == "problems=\n"


def test_emit_github_output_is_a_noop_outside_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    main.emit_github_output(["コミックガルド"])
    assert "GITHUB_OUTPUT" not in os.environ
