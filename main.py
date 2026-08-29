"""8 つのウェブマンガ出版社のシリーズ一覧を巡回し、各シリーズの `?free_only=1`
付き RSS URL を 1 本の Atom フィード (feeds/rss.xml) と HTML 索引
(feeds/index.html) にまとめる。

出版社ごとに parse_* 関数を 1 つ持つ構成にしてある。上流の HTML が変わったら
その 1 関数だけを直せばよく、フィクスチャを使ったテストもそこだけで閉じる。
セレクタや ID の取り出し方を共通テーブルに畳まないのは意図的で、
出版社ごとの差 (`%2F` エンコード済み URL と生の `/` など) を残すため。
"""

import os
import re
import sys
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import feedgenerator
import requests
from bs4 import BeautifulSoup, Tag
from jinja2 import Environment, FileSystemLoader

OUTPUT_DIR = Path("feeds")
TEMPLATE_DIR = Path("templates")
SITE_URL = "https://hanwarai.github.io/free-only-rss/"
REQUEST_TIMEOUT = 10

# 全エントリ共通の固定日付。このフィードは「新着シリーズ」を知らせるものではなく
# シリーズ別購読 URL のカタログなので、日付が動いてリーダーに再取得させたくない。
UPDATED_DATE = datetime(2025, 1, 1)

# コミックガルドの li が持つ唯一のクラス。`s{series_id}` は series id 由来で
# ビルドハッシュではないため、CSS Modules 化した現行 HTML で唯一安定した足場。
GARDO_ID_CLASS = re.compile(r"^s([0-9]+)$")


@dataclass(frozen=True)
class Series:
    """1 シリーズ分の購読情報。"""

    series_id: str
    title: str


@dataclass(frozen=True)
class Publisher:
    """1 出版社分の巡回定義。"""

    label: str
    list_url: str
    feed_host: str
    parse: Callable[[str], list[Series]]

    def feed_url(self, series_id: str) -> str:
        """シリーズ別 RSS の URL。`?free_only=1` がこのプロジェクトの本体。"""
        return f"{self.feed_host}/rss/series/{series_id}?free_only=1"


#
# HTML から必須要素を取り出すヘルパー。
#
# いずれも「見つからなければ例外」で統一している。セレクタが上流の変更で外れた
# ことを黙って 0 件や None 混じりのエントリとして通さず、その出版社の取得失敗
# として scrape() に握らせるため。
#
def _tag(element: Tag, name: str, **attrs: Any) -> Tag:
    found = element.find(name, **attrs)
    if not isinstance(found, Tag):
        raise LookupError(f"<{name}> が見つからない: {element!s:.120}")
    return found


def _text(element: Tag, name: str, **attrs: Any) -> str:
    return _tag(element, name, **attrs).text.strip()


def _attr(element: Tag, name: str) -> str:
    value = element.get(name)
    if not isinstance(value, str):
        raise LookupError(f"属性 {name} が見つからない: {element!s:.120}")
    return value


def _img_attr(element: Tag, name: str) -> str:
    return _attr(_tag(element, "img"), name)


def _class_group(element: Tag, pattern: re.Pattern[str]) -> str:
    """pattern に完全一致するクラストークンの 1 つ目のキャプチャを返す。"""
    classes: str | list[str] = element.get("class") or []
    tokens = classes.split() if isinstance(classes, str) else classes
    for token in tokens:
        matched = pattern.fullmatch(token)
        if matched:
            return matched.group(1)
    raise LookupError(f"{pattern.pattern} に一致するクラスがない: {element!s:.120}")


#
# 出版社ごとのパーサ。1 出版社 1 関数。
#
def parse_comic_days(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_attr(item, "data-series-id"), _text(item, "h4", class_="daily-series-title"))
        for item in soup.find_all("li", class_="daily-series-item")
    )


def parse_shonenjumpplus(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_id_from_url(_img_attr(item, "data-src"), "%2F"), _text(item, "h2"))
        for item in soup.find_all("li", class_="series-list-item")
    )


def parse_sunday_webry(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_id_from_url(_img_attr(item, "data-src"), "%2F"), _text(item, "h4"))
        for item in soup.find_all("li", class_="webry-series-item")
    )


def parse_tonarinoyj(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_attr(item, "id").replace("series-", ""), _text(item, "h4", class_="title"))
        for item in soup.find_all("li", class_="subpage-table-list-item")
    )


def parse_kuragebunch(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_id_from_url(_img_attr(item, "data-src"), "%2F"), _text(item, "h4"))
        for item in soup.find_all("li", class_="page-series-list-item")
    )


def parse_comic_gardo(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_class_group(item, GARDO_ID_CLASS), _text(item, "h5"))
        for item in soup.find_all("li", class_=GARDO_ID_CLASS)
    )


def parse_comic_action(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_id_from_url(_img_attr(item, "src"), "%2F"), _text(item, "h3"))
        for item in soup.find_all("li", class_=re.compile("^SeriesListItem_item__"))
    )


def parse_comic_earthstar(html: str) -> list[Series]:
    soup = BeautifulSoup(html, "html.parser")
    return _dedupe(
        Series(_id_from_url(_img_attr(item, "src"), "/"), _text(item, "h3"))
        for item in soup.select("ul[class^=SeriesList_series_list__] li")
    )


def _id_from_url(url: str, separator: str) -> str:
    """サムネイル URL の末尾セグメントから series id を取り出す。

    区切りが `%2F` と `/` の 2 種類あるのは上流がそれぞれそう出しているため。
    どちらかに正規化しないこと。
    """
    return url.rsplit(separator, maxsplit=1)[-1].split("-", maxsplit=1)[0]


def _dedupe(series: Iterable[Series]) -> list[Series]:
    """同じ series_id の重複を落とす。初出の順序は保つ。

    一覧ページによっては同じシリーズをおすすめ枠と五十音順枠の両方に出す。
    """
    unique: dict[str, Series] = {}
    for item in series:
        unique.setdefault(item.series_id, item)
    return list(unique.values())


PUBLISHERS: tuple[Publisher, ...] = (
    Publisher(
        "COMIC DAYS",
        "https://comic-days.com/series",
        "https://comic-days.com",
        parse_comic_days,
    ),
    Publisher(
        "少年ジャンプ＋",
        "https://shonenjumpplus.com/series",
        "https://shonenjumpplus.com",
        parse_shonenjumpplus,
    ),
    Publisher(
        "サンデーうぇぶり",
        "https://www.sunday-webry.com/series",
        "https://www.sunday-webry.com",
        parse_sunday_webry,
    ),
    Publisher(
        "となりのヤングジャンプ",
        "https://tonarinoyj.jp/series",
        "https://tonarinoyj.jp",
        parse_tonarinoyj,
    ),
    Publisher(
        "くらげバンチ",
        "https://kuragebunch.com/series/kuragebunch",
        "https://kuragebunch.com",
        parse_kuragebunch,
    ),
    Publisher(
        "コミックガルド",
        "https://comic-gardo.com/series",
        "https://comic-gardo.com",
        parse_comic_gardo,
    ),
    Publisher(
        "Webアクション",
        "https://comic-action.com/series",
        "https://comic-action.com",
        parse_comic_action,
    ),
    Publisher(
        "コミック アース・スター",
        "https://comic-earthstar.com/series",
        "https://comic-earthstar.com",
        parse_comic_earthstar,
    ),
)

# 出版社ごとの取得結果。None は取得失敗 (例外)、空リストは 0 件 (selector 脱落)。
ScrapeResult = list[tuple[Publisher, list[Series] | None]]


def fetch(url: str, *, ssl_verify: bool = True) -> str:
    response = requests.get(
        url,
        verify=ssl_verify,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": ""},
    )
    # エラーページを HTML として食わせると 0 件になり「selector が外れた」と
    # 誤診する。HTTP エラーは取得失敗としてここで分ける。
    response.raise_for_status()
    return response.text


def scrape(publisher: Publisher, *, ssl_verify: bool = True) -> list[Series] | None:
    try:
        return publisher.parse(fetch(publisher.list_url, ssl_verify=ssl_verify))
    except Exception as error:
        print(f"[ERROR] {publisher.label}: {type(error).__name__}: {error}", file=sys.stderr)
        return None


def collect(publishers: Sequence[Publisher], *, ssl_verify: bool = True) -> ScrapeResult:
    return [(publisher, scrape(publisher, ssl_verify=ssl_verify)) for publisher in publishers]


def build_feed(results: ScrapeResult) -> tuple[feedgenerator.Atom1Feed, list[dict[str, Any]]]:
    """Atom フィードと index.html 用の出版社リストを組み立てる。"""
    rss = feedgenerator.Atom1Feed(
        title="free-only-rss",
        link=SITE_URL,
        description="",
        language="ja",
    )
    sites: list[dict[str, Any]] = []
    for publisher, series_list in results:
        if series_list is None:
            continue
        feeds = []
        for series in series_list:
            url = publisher.feed_url(series.series_id)
            rss.add_item(
                unique_id=series.series_id,
                title=series.title,
                link=url,
                description="",
                content="",
                updateddate=UPDATED_DATE,
            )
            feeds.append({"title": series.title, "url": url})
        sites.append({"title": publisher.label, "feeds": feeds})
    return rss, sites


def report(results: ScrapeResult, *, github_actions: bool = False) -> list[str]:
    """出版社ごとの件数を出し、問題のあった出版社の label を返す。

    scrape() は例外しか握らないので「selector が外れて 0 件」は素通りする。
    実際コミックガルドはこれで無言のままフィードから欠落していた。1 社壊れても
    残りの配信は続けたいので run は落とさず、警告として可視化するに留める。
    """
    problems = []
    for publisher, series_list in results:
        count = 0 if series_list is None else len(series_list)
        print(f"{publisher.label}: {count} series")
        if count:
            continue
        if series_list is None:
            reason = "取得失敗 — 上の [ERROR] を参照"
        else:
            reason = "0 件 — selector が上流の HTML 変更で外れた可能性"
        problems.append(publisher.label)
        print(f"[WARN] {publisher.label}: {reason}", file=sys.stderr)
        if github_actions:
            print(f"::warning title={publisher.label}::{reason}")
    return problems


def write_outputs(
    rss: feedgenerator.Atom1Feed,
    sites: Sequence[dict[str, Any]],
    output_dir: Path = OUTPUT_DIR,
    template_dir: Path = TEMPLATE_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "rss.xml").open("w", encoding="utf-8") as feed_file:
        rss.write(feed_file, "utf-8")

    jinja_env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
    rendered = jinja_env.get_template("index.html").render(sites=sites)
    (output_dir / "index.html").write_text(rendered, encoding="utf-8")


def main() -> int:
    ssl_verify = os.getenv("SSL_VERIFY", "True") == "True"
    github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    results = collect(PUBLISHERS, ssl_verify=ssl_verify)
    rss, sites = build_feed(results)
    report(results, github_actions=github_actions)
    write_outputs(rss, sites)
    # 1 社壊れても残り 7 社の配信は続けたいので、意図して exit 0 のままにする。
    return 0


if __name__ == "__main__":
    sys.exit(main())
