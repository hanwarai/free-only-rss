import json
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixture_html() -> Callable[[str], str]:
    """tests/fixtures/{name}.html を読む。"""

    def load(name: str) -> str:
        return (FIXTURE_DIR / f"{name}.html").read_text(encoding="utf-8")

    return load


@pytest.fixture
def expected_series() -> dict[str, list[list[str]]]:
    """フィクスチャから読み取れるべき (series_id, title) のスナップショット。"""
    data = json.loads((FIXTURE_DIR / "expected.json").read_text(encoding="utf-8"))
    return dict(data)
