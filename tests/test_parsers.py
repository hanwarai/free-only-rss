"""出版社ごとの parse_* が実サイトの HTML をどう読むかを固定する。

tests/fixtures/*.html は各シリーズ一覧ページから一致要素を 3 件だけ切り出した
実物で、tests/fixtures/expected.json がそこから読めるべき (series_id, title)。
手書き HTML ではなく実物を使うのは、上流が CSS Modules 化してセレクタが黙って
外れる ―― 実際にコミックガルドで起きた ―― のがこのプロジェクト唯一の障害
モードだから。フィクスチャを貼り替えたら expected.json も貼り替える。
"""

from collections.abc import Callable

import pytest

import main

Parser = Callable[[str], list[main.Series]]

PARSERS: list[tuple[str, Parser]] = [
    ("comic_days", main.parse_comic_days),
    ("shonenjumpplus", main.parse_shonenjumpplus),
    ("sunday_webry", main.parse_sunday_webry),
    ("tonarinoyj", main.parse_tonarinoyj),
    ("kuragebunch", main.parse_kuragebunch),
    ("comic_gardo", main.parse_comic_gardo),
    ("comic_action", main.parse_comic_action),
    ("comic_earthstar", main.parse_comic_earthstar),
]


def test_every_publisher_has_a_parser_test() -> None:
    """PUBLISHERS に足したのにテストを足し忘れる事故を防ぐ。"""
    assert {parser for _, parser in PARSERS} == {p.parse for p in main.PUBLISHERS}


@pytest.mark.parametrize(("name", "parser"), PARSERS)
def test_parses_series_from_real_html(
    name: str,
    parser: Parser,
    fixture_html: Callable[[str], str],
    expected_series: dict[str, list[list[str]]],
) -> None:
    parsed = parser(fixture_html(name))
    assert [[s.series_id, s.title] for s in parsed] == expected_series[name]


@pytest.mark.parametrize(("name", "parser"), PARSERS)
def test_returns_empty_when_selector_matches_nothing(name: str, parser: Parser) -> None:
    """セレクタが外れたら例外ではなく 0 件。report() がこれを警告に変える。"""
    assert parser("<!doctype html><html><body><ul></ul></body></html>") == []


@pytest.mark.parametrize(("name", "parser"), PARSERS)
def test_deduplicates_series_listed_twice(
    name: str,
    parser: Parser,
    fixture_html: Callable[[str], str],
    expected_series: dict[str, list[list[str]]],
) -> None:
    """おすすめ枠と五十音順枠のように同じシリーズが 2 度出ても 1 件にする。"""
    html = fixture_html(name)
    parsed = parser(html + html)
    assert [[s.series_id, s.title] for s in parsed] == expected_series[name]


@pytest.mark.parametrize(("name", "parser"), PARSERS)
def test_series_ids_are_usable_in_a_feed_url(
    name: str,
    parser: Parser,
    fixture_html: Callable[[str], str],
) -> None:
    for series in parser(fixture_html(name)):
        assert series.series_id
        assert "/" not in series.series_id
        assert "%" not in series.series_id
        assert series.title == series.title.strip()
        assert series.title
