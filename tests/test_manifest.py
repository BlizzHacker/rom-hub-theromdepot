import importlib
import json
from pathlib import Path

import pytest

from rom_hub.manifest import SUPPORTED_CONFIG_TYPES, load_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.toml"
CATALOG_PATH = ROOT / "catalog" / "plugins.json"


@pytest.fixture(scope="module")
def manifest():
    return load_manifest(MANIFEST_PATH)


def test_the_host_can_parse_this_manifest():
    load_manifest(MANIFEST_PATH)


def test_every_config_type_is_supported(manifest):
    assert all(spec["type"] in SUPPORTED_CONFIG_TYPES
               for spec in manifest.config_schema.values())


def test_entrypoints_resolve_to_classes(manifest):
    for entrypoint in manifest.capabilities.values():
        module, _, name = entrypoint.partition(":")
        assert isinstance(getattr(importlib.import_module(module), name), type)


def test_manifest_declares_only_search_and_browser_handoff(manifest):
    assert set(manifest.capabilities) == {"search", "stream"}
    assert "importer" not in manifest.capabilities


def test_manifest_never_requests_a_password_or_cookie(manifest):
    assert not ({"password", "cookie", "session", "username"} & set(manifest.config_schema))
    assert manifest.config_schema["catalog_path"]["default"] == ""


def test_catalog_entry_matches_manifest(manifest):
    entry = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["plugins"][0]
    assert entry["slug"] == manifest.slug
    assert entry["version"] == manifest.version
    assert entry["rpp_version"] == manifest.rpp_version
    assert sorted(entry["capabilities"]) == sorted(manifest.capabilities)
    assert sorted(entry["network"]) == sorted(manifest.network)


def test_catalog_platforms_are_exactly_the_implemented_mapping():
    from theromdepot.platforms import PLATFORM_ALIASES

    entry = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))["plugins"][0]
    assert set(entry["platforms"]) == set(PLATFORM_ALIASES.values())
