"""HTML 取り出しヘルパーの仕様。

いずれも「必須要素が無ければ LookupError」で統一してある。0 件や None 混じりの
エントリを黙って通さず、その出版社の取得失敗として scrape() に握らせるため。
"""

import re

import pytest
from bs4 import BeautifulSoup, Tag

import main


def _soup(html: str) -> Tag:
    parsed = BeautifulSoup(html, "html.parser")
    element = parsed.find("li")
    assert isinstance(element, Tag)
    return element


def test_tag_returns_matching_child() -> None:
    assert main._tag(_soup("<li><h4>x</h4></li>"), "h4").text == "x"


def test_tag_honours_attribute_filters() -> None:
    element = _soup('<li><h4 class="a">A</h4><h4 class="b">B</h4></li>')
    assert main._tag(element, "h4", class_="b").text == "B"


def test_tag_raises_when_child_is_missing() -> None:
    with pytest.raises(LookupError, match="h4"):
        main._tag(_soup("<li><h5>x</h5></li>"), "h4")


def test_text_strips_surrounding_whitespace() -> None:
    assert main._text(_soup("<li><h4>  x\n </h4></li>"), "h4") == "x"


def test_attr_returns_string_attribute() -> None:
    assert main._attr(_soup('<li data-series-id="42"></li>'), "data-series-id") == "42"


def test_attr_raises_when_attribute_is_missing() -> None:
    with pytest.raises(LookupError, match="data-series-id"):
        main._attr(_soup("<li></li>"), "data-series-id")


def test_attr_raises_for_multi_valued_attributes() -> None:
    """class は list で返るため、id の取り出しには使わせない。"""
    with pytest.raises(LookupError, match="class"):
        main._attr(_soup('<li class="a b"></li>'), "class")


def test_img_attr_reads_the_thumbnail_url() -> None:
    element = _soup('<li><img data-src="https://e/x%2F99-w.jpg"></li>')
    assert main._img_attr(element, "data-src") == "https://e/x%2F99-w.jpg"


def test_img_attr_raises_when_there_is_no_image() -> None:
    with pytest.raises(LookupError, match="img"):
        main._img_attr(_soup("<li></li>"), "src")


def test_class_group_returns_the_captured_series_id() -> None:
    element = _soup('<li class="SeriesListItem_item__hash s12345"></li>')
    assert main._class_group(element, main.GARDO_ID_CLASS) == "12345"


def test_class_group_ignores_position_of_the_matching_token() -> None:
    """ハッシュ付きクラスが後ろに増えても壊れないこと (末尾決め打ちにしない)。"""
    element = _soup('<li class="s777 Foo_bar__hash"></li>')
    assert main._class_group(element, main.GARDO_ID_CLASS) == "777"


def test_class_group_accepts_a_single_class_string() -> None:
    element = BeautifulSoup('<li class="s1"></li>', "html.parser")
    tag = element.find("li")
    assert isinstance(tag, Tag)
    tag.attrs["class"] = "s1"
    assert main._class_group(tag, main.GARDO_ID_CLASS) == "1"


def test_class_group_raises_when_no_token_matches() -> None:
    with pytest.raises(LookupError, match=re.escape(main.GARDO_ID_CLASS.pattern)):
        main._class_group(_soup('<li class="series"></li>'), main.GARDO_ID_CLASS)


def test_class_group_raises_when_there_is_no_class() -> None:
    with pytest.raises(LookupError):
        main._class_group(_soup("<li></li>"), main.GARDO_ID_CLASS)


@pytest.mark.parametrize(
    ("url", "separator", "expected"),
    [
        ("https://e/i/%2F1234-w.jpg", "%2F", "1234"),
        ("https://e/i/1234-w.jpg", "/", "1234"),
        # 区切りが %2F と生の / の 2 種類あるのは上流がそれぞれそう出しているため。
        # 逆の区切りを渡すと別物が返る。正規化してはいけない理由がこれ。
        ("https://e/i/%2F1234-w.jpg", "/", "%2F1234"),
    ],
)
def test_id_from_url(url: str, separator: str, expected: str) -> None:
    assert main._id_from_url(url, separator) == expected


def test_dedupe_keeps_the_first_occurrence_in_order() -> None:
    series = [
        main.Series("1", "one"),
        main.Series("2", "two"),
        main.Series("1", "one (recommended)"),
        main.Series("3", "three"),
    ]
    assert main._dedupe(series) == [
        main.Series("1", "one"),
        main.Series("2", "two"),
        main.Series("3", "three"),
    ]
