"""件数サマリと警告。

scrape() は例外しか握らないので「selector が外れて 0 件」は素通りする。
実際コミックガルドはこれで無言のままフィードから欠落していた。ここはその
再発を検知する唯一の経路なので、3 経路 (正常 / 0 件 / 取得失敗) を固定する。
"""

import pytest

import main

DAYS = main.Publisher("COMIC DAYS", "https://d.test/series", "https://d.test", lambda html: [])
GARDO = main.Publisher("コミックガルド", "https://g.test/series", "https://g.test", lambda html: [])


def test_reports_counts_for_every_publisher(capsys: pytest.CaptureFixture[str]) -> None:
    results: main.ScrapeResult = [(DAYS, [main.Series("1", "あ")]), (GARDO, [])]
    main.report(results)
    captured = capsys.readouterr()
    assert "COMIC DAYS: 1 series" in captured.out
    assert "コミックガルド: 0 series" in captured.out


def test_healthy_publisher_produces_no_problem(capsys: pytest.CaptureFixture[str]) -> None:
    assert main.report([(DAYS, [main.Series("1", "あ")])]) == []
    assert capsys.readouterr().err == ""


def test_zero_hits_are_reported_as_a_selector_problem(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main.report([(GARDO, [])]) == ["コミックガルド"]
    assert "[WARN] コミックガルド: 0 件" in capsys.readouterr().err


def test_fetch_failure_is_reported_differently_from_zero_hits(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """None は取得失敗。0 件と同じ文言だと selector を無駄に疑うことになる。"""
    assert main.report([(GARDO, None)]) == ["コミックガルド"]
    assert "[WARN] コミックガルド: 取得失敗" in capsys.readouterr().err


def test_emits_actions_annotation_only_under_ci(capsys: pytest.CaptureFixture[str]) -> None:
    main.report([(GARDO, [])], github_actions=True)
    assert "::warning title=コミックガルド::0 件" in capsys.readouterr().out

    main.report([(GARDO, [])], github_actions=False)
    assert "::warning" not in capsys.readouterr().out
