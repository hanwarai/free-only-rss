"""取得と失敗の分類。

scrape() の戻り値は 3 状態ある: 件数のあるリスト / 空リスト (selector 脱落) /
None (取得失敗)。report() がこの 3 つを別のメッセージに振り分けるので、
ここが崩れると障害の切り分けができなくなる。
"""

import pytest
import requests
from requests_mock import Mocker

import main

URL = "https://example.test/series"


def _publisher(parse: object = None) -> main.Publisher:
    return main.Publisher(
        label="テスト出版社",
        list_url=URL,
        feed_host="https://example.test",
        parse=parse or (lambda html: [main.Series("1", html.strip())]),  # type: ignore[arg-type]
    )


def test_fetch_returns_the_body(requests_mock: Mocker) -> None:
    requests_mock.get(URL, text="<html>ok</html>")
    assert main.fetch(URL) == "<html>ok</html>"


def test_fetch_sends_an_empty_user_agent(requests_mock: Mocker) -> None:
    """上流が既定の python-requests UA を弾くため空文字を送っている。"""
    requests_mock.get(URL, text="ok")
    main.fetch(URL)
    assert requests_mock.last_request is not None
    assert requests_mock.last_request.headers["User-Agent"] == ""


def test_fetch_honours_ssl_verify(requests_mock: Mocker) -> None:
    requests_mock.get(URL, text="ok")
    main.fetch(URL, ssl_verify=False)
    assert requests_mock.last_request is not None
    assert requests_mock.last_request.verify is False


def test_fetch_raises_on_http_error(requests_mock: Mocker) -> None:
    """エラーページを HTML として食うと 0 件になり「selector が外れた」と誤診する。"""
    requests_mock.get(URL, status_code=503, text="<html>maintenance</html>")
    with pytest.raises(requests.HTTPError):
        main.fetch(URL)


def test_scrape_returns_parsed_series(requests_mock: Mocker) -> None:
    requests_mock.get(URL, text="body")
    assert main.scrape(_publisher()) == [main.Series("1", "body")]


def test_scrape_returns_empty_list_when_selector_matches_nothing(requests_mock: Mocker) -> None:
    requests_mock.get(URL, text="body")
    assert main.scrape(_publisher(parse=lambda html: [])) == []


def test_scrape_returns_none_on_http_error(
    requests_mock: Mocker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requests_mock.get(URL, status_code=500, text="boom")
    assert main.scrape(_publisher()) is None
    assert "[ERROR] テスト出版社: HTTPError" in capsys.readouterr().err


def test_scrape_returns_none_on_connection_error(
    requests_mock: Mocker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requests_mock.get(URL, exc=requests.ConnectionError("unreachable"))
    assert main.scrape(_publisher()) is None
    assert "[ERROR] テスト出版社: ConnectionError: unreachable" in capsys.readouterr().err


def test_scrape_returns_none_when_a_required_element_is_missing(
    requests_mock: Mocker,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """途中で 1 件でも壊れていたら、その出版社は部分結果ではなく取得失敗にする。"""

    def parse(html: str) -> list[main.Series]:
        raise LookupError("<h4> が見つからない")

    requests_mock.get(URL, text="body")
    assert main.scrape(_publisher(parse=parse)) is None
    assert "[ERROR] テスト出版社: LookupError" in capsys.readouterr().err


def test_collect_keeps_publisher_order(requests_mock: Mocker) -> None:
    first = _publisher()
    second = main.Publisher(
        label="2 社目",
        list_url="https://other.test/series",
        feed_host="https://other.test",
        parse=lambda html: [],
    )
    requests_mock.get(URL, text="a")
    requests_mock.get("https://other.test/series", text="b")
    assert main.collect([first, second]) == [(first, [main.Series("1", "a")]), (second, [])]
