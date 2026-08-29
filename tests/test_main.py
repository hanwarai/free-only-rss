"""main() の通し。8 社ぶんのフィクスチャを requests_mock で返して結線を確かめる。"""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from requests_mock import Mocker

import main

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fixture_name(publisher: main.Publisher) -> str:
    return publisher.parse.__name__.removeprefix("parse_")


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """feeds/ を汚さないよう、テンプレートを持った空ディレクトリで走らせる。"""
    shutil.copytree(REPO_ROOT / "templates", tmp_path / "templates")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def all_publishers_served(
    requests_mock: Mocker,
    fixture_html: Callable[[str], str],
) -> Mocker:
    for publisher in main.PUBLISHERS:
        requests_mock.get(publisher.list_url, text=fixture_html(_fixture_name(publisher)))
    return requests_mock


def test_writes_both_outputs_for_every_publisher(
    workspace: Path,
    all_publishers_served: Mocker,
    expected_series: dict[str, list[list[str]]],
) -> None:
    assert main.main() == 0

    feed = (workspace / "feeds" / "rss.xml").read_text(encoding="utf-8")
    index = (workspace / "feeds" / "index.html").read_text(encoding="utf-8")
    total = sum(len(v) for v in expected_series.values())
    assert feed.count("<entry>") == total
    assert feed.count("?free_only=1") == total
    for publisher in main.PUBLISHERS:
        assert f"<h2>{publisher.label}</h2>" in index


def test_ssl_verify_env_var_reaches_the_request(
    workspace: Path,
    all_publishers_served: Mocker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SSL_VERIFY", "False")
    main.main()
    assert all_publishers_served.last_request is not None
    assert all_publishers_served.last_request.verify is False


def test_one_broken_publisher_does_not_stop_the_others(
    workspace: Path,
    all_publishers_served: Mocker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """1 社壊れても残りの配信は続ける。ここが exit 0 のままである理由。"""
    broken = main.PUBLISHERS[0]
    all_publishers_served.get(broken.list_url, status_code=500, text="boom")

    assert main.main() == 0

    captured = capsys.readouterr()
    assert f"[ERROR] {broken.label}" in captured.err
    assert f"[WARN] {broken.label}: 取得失敗" in captured.err
    index = (workspace / "feeds" / "index.html").read_text(encoding="utf-8")
    assert f"<h2>{broken.label}</h2>" not in index
    assert f"<h2>{main.PUBLISHERS[1].label}</h2>" in index


def test_zero_hits_are_annotated_for_actions(
    workspace: Path,
    all_publishers_served: Mocker,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """0 件は run を落とさないので、Actions のアノテーションが唯一の可視化経路。"""
    silent = main.PUBLISHERS[5]
    all_publishers_served.get(silent.list_url, text="<html><body></body></html>")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert main.main() == 0

    captured = capsys.readouterr()
    assert f"::warning title={silent.label}::0 件" in captured.out
    assert f"[WARN] {silent.label}: 0 件" in captured.err
    index = (workspace / "feeds" / "index.html").read_text(encoding="utf-8")
    assert f"<h2>{silent.label}</h2>" in index


def test_healthy_run_emits_no_warnings(
    workspace: Path,
    all_publishers_served: Mocker,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert main.main() == 0
    captured = capsys.readouterr()
    assert "::warning" not in captured.out
    assert captured.err == ""
