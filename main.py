import os
import re

import feedgenerator
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

SSL_VERIFY = os.getenv('SSL_VERIFY', 'True') == 'True'
sites = []

rss = feedgenerator.Atom1Feed(
    title='free-only-rss',
    link='https://hanwarai.github.io/free-only-rss/',
    description='',
    language="ja",
)

#
# COMIC DAYS
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://comic-days.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'COMIC DAYS', 'feeds': feeds})

#
# 少年ジャンプ＋
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://shonenjumpplus.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': '少年ジャンプ＋', 'feeds': feeds})

#
# サンデーうぇぶり
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://www.sunday-webry.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'サンデーうぇぶり', 'feeds': feeds})

#
# となりのヤングジャンプ
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://tonarinoyj.jp/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'となりのヤングジャンプ', 'feeds': feeds})

#
# くらげバンチ
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://kuragebunch.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'くらげバンチ', 'feeds': feeds})

#
# コミックガルド
#
site = requests.get('https://comic-gardo.com/series', verify=SSL_VERIFY, timeout=10, headers={'User-Agent': ''})
soup = BeautifulSoup(site.text, 'html.parser')
feeds = []
unique_ids = []
for series in soup.find_all('li', class_="series-section-item"):
    series_id = series.get('class')[-1].replace('s', '')
    if series_id in unique_ids:
        continue
    unique_ids.append(series_id)
    title = series.find('h5', class_='series-title').text.strip()
    rss.add_item(
        unique_id=series_id,
        title=title,
        link='https://comic-gardo.com/rss/series/' + series_id + '?free_only=1',
        description="",
        content=""
    )
    feeds.append({'title': title, 'url': 'https://comic-gardo.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'コミックガルド', 'feeds': feeds})

#
# Webアクション
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://comic-action.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'Webアクション', 'feeds': feeds})

#
# コミック アース・スター
#
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
        content=""
    )
    feeds.append({'title': title, 'url': 'https://comic-earthstar.com/rss/series/' + series_id + '?free_only=1'})
sites.append({'title': 'コミック アース・スター', 'feeds': feeds})

# rss feed
with open('feeds/rss.xml', 'w') as fp:
    rss.write(fp, 'utf-8')

# Generate index.html
jinja_env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True
)
jinja_template = jinja_env.get_template('index.html')
index = open('feeds/index.html', 'w')
index.write(jinja_template.render(sites=sites))
