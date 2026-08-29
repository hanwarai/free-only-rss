"""Atom フィードと index.html 用データの組み立て。"""

import xml.etree.ElementTree as ET
from io import StringIO

import main

ATOM = "{http://www.w3.org/2005/Atom}"

DAYS = main.Publisher(
    label="COMIC DAYS",
    list_url="https://comic-days.com/series",
    feed_host="https://comic-days.com",
    parse=lambda html: [],
)
JUMP = main.Publisher(
    label="少年ジャンプ＋",
    list_url="https://shonenjumpplus.com/series",
    feed_host="https://shonenjumpplus.com",
    parse=lambda html: [],
)


def _links(rss: main.feedgenerator.Atom1Feed) -> list[str]:
    buffer = StringIO()
    rss.write(buffer, "utf-8")
    root = ET.fromstring(buffer.getvalue())
    return [
        link.attrib["href"]
        for entry in root.findall(f"{ATOM}entry")
        for link in entry.findall(f"{ATOM}link")
    ]


def test_feed_url_carries_the_free_only_query() -> None:
    assert DAYS.feed_url("42") == "https://comic-days.com/rss/series/42?free_only=1"


def test_builds_one_entry_per_series() -> None:
    results: main.ScrapeResult = [(DAYS, [main.Series("1", "あ"), main.Series("2", "い")])]
    rss, sites = main.build_feed(results)
    assert _links(rss) == [
        "https://comic-days.com/rss/series/1?free_only=1",
        "https://comic-days.com/rss/series/2?free_only=1",
    ]
    assert sites == [
        {
            "title": "COMIC DAYS",
            "feeds": [
                {"title": "あ", "url": "https://comic-days.com/rss/series/1?free_only=1"},
                {"title": "い", "url": "https://comic-days.com/rss/series/2?free_only=1"},
            ],
        }
    ]


def test_skips_publishers_that_failed_to_load() -> None:
    """取得失敗した出版社は index.html にも空セクションを作らない。"""
    results: main.ScrapeResult = [(DAYS, None), (JUMP, [main.Series("9", "う")])]
    rss, sites = main.build_feed(results)
    assert _links(rss) == ["https://shonenjumpplus.com/rss/series/9?free_only=1"]
    assert [site["title"] for site in sites] == ["少年ジャンプ＋"]


def test_keeps_a_publisher_that_returned_nothing() -> None:
    """0 件は「取得はできた」なので、見出しだけのセクションとして残す。"""
    _, sites = main.build_feed([(DAYS, [])])
    assert sites == [{"title": "COMIC DAYS", "feeds": []}]


def test_all_entries_share_the_fixed_updated_date() -> None:
    """新着通知が目的ではないので、日付が動いてリーダーに再取得させない。"""
    rss, _ = main.build_feed([(DAYS, [main.Series("1", "あ"), main.Series("2", "い")])])
    buffer = StringIO()
    rss.write(buffer, "utf-8")
    root = ET.fromstring(buffer.getvalue())
    updated = {entry.findtext(f"{ATOM}updated") for entry in root.findall(f"{ATOM}entry")}
    assert updated == {"2025-01-01T00:00:00Z"}
