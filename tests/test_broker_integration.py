"""Exercise the plugin across the real RPP subprocess boundary."""

from pathlib import Path

from rom_hub.broker.host import PluginProcess
from rom_hub.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[1]


class NoFetcher:
    def get(self, *args, **kwargs):
        raise AssertionError("browser-assisted search must never invoke the host fetcher")


def test_search_and_browser_handoff_cross_the_real_broker(catalog_path):
    manifest = load_manifest(ROOT / "manifest.toml")
    with PluginProcess(
        ROOT,
        manifest,
        {"catalog_path": str(catalog_path)},
        NoFetcher(),
        allow_unsandboxed=True,
    ) as process:
        results = process.search("mario party", "n64", 5)
        assert len(results) == 1
        assert results[0].plugin == "theromdepot"

        target = process.resolve_stream(results[0])
        assert target.kind == "url"
        assert target.target == results[0].url
        assert target.extra["login_required"] == "true"
