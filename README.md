# free-only-rss

8 つのウェブマンガ出版社のシリーズ一覧を巡回し、**各シリーズの「無料話だけ」の RSS URL** (`?free_only=1`) を 1 本の Atom フィードにまとめて配信する。GitHub Actions が 12 時間ごとに実行し、GitHub Pages へ公開する。

- 一覧ページ: https://hanwarai.github.io/free-only-rss/
- まとめフィード: https://hanwarai.github.io/free-only-rss/rss.xml

一覧ページの各行にある `/feed subscribe` ボタンで、そのシリーズの購読コマンドがクリップボードに入る。

## 対象

COMIC DAYS / 少年ジャンプ＋ / サンデーうぇぶり / となりのヤングジャンプ / くらげバンチ / コミックガルド / Webアクション / コミック アース・スター

いずれも `https://{host}/rss/series/{series_id}?free_only=1` というシリーズ別 RSS を持つ。このプロジェクトがやるのは、その URL を全シリーズぶん集めて配ること。

## 仕組み

```
各社の /series → main.py → feeds/rss.xml + feeds/index.html → GitHub Pages
```

出版社ごとに `parse_*` 関数を 1 つ持ち、`PUBLISHERS` に並べてある。上流の HTML が変わったらその関数だけを直す。1 社が壊れても残りの配信は止めず、件数 0 の出版社は警告として可視化する。

## 開発

```bash
uv sync --all-extras          # 依存インストール
uv run main.py                # フィード生成 (feeds/ 配下に出力)
uv run pytest                 # テスト (カバレッジ 80% 未満で失敗)
uv run ruff check .           # lint
uv run ruff format .          # フォーマット
uv run mypy                   # 型検査
uv run pre-commit install     # コミット時に上記を自動実行
```

Python 3.13 / パッケージマネージャーは [uv](https://docs.astral.sh/uv/)。設計上の判断は [CLAUDE.md](CLAUDE.md) に書いてある。
