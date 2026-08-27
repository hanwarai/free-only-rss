import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime

import feedgenerator
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

SSL_VERIFY = os.getenv('SSL_VERIFY', 'True') == 'True'
GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'
sites = []
# scrape() を通った出版社。末尾のサマリで sites と突き合わせ、
# 例外で落ちた場合と 0 件だった場合の両方を検知するために使う。
scraped = []


@contextmanager
def scrape(label):
    scraped.append(label)
    try:
        yield
    except Exception as e:
        print(f'[ERROR] {label}: {type(e).__name__}: {e}', file=sys.stderr)

rss = feedgenerator.Atom1Feed(
    title='free-only-rss',
    link='https://hanwarai.github.io/free-only-rss/',
    description='',
    language="ja",
)

#
# COMIC DAYS
#
with scrape('COMIC DAYS'):
    site = requests.get('https://comic-days.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_="daily-series-item"):
        series_id = series.get('data-series-id')
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h4', class_='daily-series-title').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://comic-days.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://comic-days.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'COMIC DAYS', 'feeds': feeds})

#
# 少年ジャンプ＋
#
with scrape('少年ジャンプ＋'):
    site = requests.get('https://shonenjumpplus.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_='series-list-item'):
        series_id = series.find('img').get('data-src').split('%2F')[-1].split('-')[0]
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h2').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://shonenjumpplus.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://shonenjumpplus.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': '少年ジャンプ＋', 'feeds': feeds})

#
# サンデーうぇぶり
#
with scrape('サンデーうぇぶり'):
    site = requests.get('https://www.sunday-webry.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_='webry-series-item'):
        series_id = series.find('img').get('data-src').split('%2F')[-1].split('-')[0]
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h4').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://www.sunday-webry.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://www.sunday-webry.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'サンデーうぇぶり', 'feeds': feeds})

#
# となりのヤングジャンプ
#
with scrape('となりのヤングジャンプ'):
    site = requests.get('https://tonarinoyj.jp/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_="subpage-table-list-item"):
        series_id = series.get('id').replace('series-', '')
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h4', class_='title').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://tonarinoyj.jp/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://tonarinoyj.jp/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'となりのヤングジャンプ', 'feeds': feeds})

#
# くらげバンチ
#
with scrape('くらげバンチ'):
    site = requests.get('https://kuragebunch.com/series/kuragebunch', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_="page-series-list-item"):
        series_id = series.find('img').get('data-src').split('%2F')[-1].split('-')[0]
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h4').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://kuragebunch.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://kuragebunch.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'くらげバンチ', 'feeds': feeds})

#
# コミックガルド
#
with scrape('コミックガルド'):
    site = requests.get('https://comic-gardo.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    # 上流が CSS Modules 化し series-section-item / series-title は消えた。
    # li 側に残るクラスは series id 由来の `s{id}` ただ 1 個 (SeriesListItem_* は子要素側)。
    # これはハッシュ付きクラスと違いデプロイ間で変わらないので、ここを基準にする。
    for series in soup.find_all('li', class_=re.compile('^s[0-9]+$')):
        series_id = series.get('class')[-1].removeprefix('s')
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h5').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://comic-gardo.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://comic-gardo.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'コミックガルド', 'feeds': feeds})

#
# Webアクション
#
with scrape('Webアクション'):
    site = requests.get('https://comic-action.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.find_all('li', class_=re.compile('^SeriesListItem_item__')):
        series_id = series.find('img').get('src').split('%2F')[-1].split('-')[0]
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h3').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://comic-action.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://comic-action.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'Webアクション', 'feeds': feeds})

#
# コミック アース・スター
#
with scrape('コミック アース・スター'):
    site = requests.get('https://comic-earthstar.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
    soup = BeautifulSoup(site.text, 'html.parser')
    feeds = []
    unique_ids = []
    for series in soup.select('ul[class^=SeriesList_series_list__] li'):
        series_id = series.find('img').get('src').split('/')[-1].split('-')[0]
        if series_id in unique_ids:
            continue
        unique_ids.append(series_id)
        title = series.find('h3').text.strip()
        rss.add_item(
            unique_id=series_id,
            title=title,
            link='https://comic-earthstar.com/rss/series/' + series_id + '?free_only=1',
            description="",
            content="",
            updateddate=datetime.strptime('2025-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
        )
        feeds.append({'title': title, 'url': 'https://comic-earthstar.com/rss/series/' + series_id + '?free_only=1'})
    sites.append({'title': 'コミック アース・スター', 'feeds': feeds})

#
# 取得結果サマリ
#
# scrape() は例外しか握らないので「selector が外れて 0 件ヒット」は素通りする。
# 実際コミックガルドはこれで無言のまま feed から欠落していた。部分的にでも
# 配信は続けたいので run は落とさず、警告として可視化するに留める。
found = {site['title']: len(site['feeds']) for site in sites}
for label in scraped:
    count = found.get(label, 0)
    print(f'{label}: {count} series')
    if count:
        continue
    # sites に載っていない = 例外で中断。載っていて 0 件 = selector が外れた。
    reason = '0 件 — selector が上流の HTML 変更で外れた可能性' if label in found else '取得失敗 — 上の [ERROR] を参照'
    print(f'[WARN] {label}: {reason}', file=sys.stderr)
    if GITHUB_ACTIONS:
        print(f'::warning title={label}::{reason}')

# rss feed
with open('feeds/rss.xml', 'w', encoding='utf-8') as fp:
    rss.write(fp, 'utf-8')

# Generate index.html
jinja_env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True
)
jinja_template = jinja_env.get_template('index.html')
with open('feeds/index.html', 'w', encoding='utf-8') as index:
    index.write(jinja_template.render(sites=sites))
