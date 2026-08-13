import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for candidate in (
    os.environ.get("ROM_HUB_SRC"),
    "/opt/rom-hub/src",
    str(ROOT.parent / "rom-hub-work" / "src"),
    str(ROOT.parent / "rom-hub" / "src"),
):
    if candidate and Path(candidate).is_dir():
        sys.path.insert(0, candidate)
        break

for candidate in (
    os.environ.get("ROMARR_SRC"),
    "/opt/romarr",
    str(ROOT.parent / "romarr-work"),
    str(ROOT.parent / "romarr"),
):
    if candidate and Path(candidate, "romarr").is_dir():
        sys.path.insert(0, candidate)
        break


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def catalog_path(fixture_dir):
    return fixture_dir / "get_contents.json"


class NoHttp:
    def get(self, *args, **kwargs):
        raise AssertionError("the browser-assisted plugin must make no HTTP request")
