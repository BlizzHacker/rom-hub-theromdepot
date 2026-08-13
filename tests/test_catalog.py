import json

import pytest

from theromdepot.catalog import (
    CatalogUnavailable,
    InvalidEntry,
    clean_path,
    display_title,
    download_url,
    entries_from,
    load_catalog,
)


def test_flattens_the_live_app_tree_shape(catalog_path):
    entries = load_catalog(catalog_path)
    assert [(entry.path, entry.platform, entry.size_bytes) for entry in entries] == [
        (
            "Nintendo 64/Europe/Mario Party (Europe) (En,Fr,De).z64",
            "n64",
            1234,
        ),
        (
            "Nintendo 64/USA/The Legend of Zelda - Ocarina of Time.z64",
            "n64",
            8104,
        ),
        (
            "Super Nintendo Entertainment System/USA/Contra III - The Alien Wars (USA).zip",
            "snes",
            2048,
        ),
    ]


def test_directories_are_not_mistaken_for_files(catalog_path):
    assert all(entry.name not in {"Nintendo 64", "Europe", "USA"}
               for entry in load_catalog(catalog_path))


def test_unknown_platform_is_dropped_instead_of_guessed(catalog_path):
    assert "Wrong Guess" not in " ".join(entry.title for entry in load_catalog(catalog_path))


def test_metadata_is_preserved(catalog_path):
    mario = load_catalog(catalog_path)[0]
    assert mario.name == "Mario Party (Europe) (En,Fr,De).z64"
    assert mario.title == "Mario Party (Europe) (En,Fr,De)"
    assert mario.platform_label == "Nintendo 64"
    assert mario.region == "Europe"
    assert mario.mtime == "2026-08-10T03:00:00.000Z"


def test_accepts_romarr_captures_normalized_shape():
    payload = {"items": [{
        "id": "Nintendo 64/Europe/Mario Party.z64",
        "title": "Mario Party",
        "name": "Mario Party.z64",
        "platform": "Nintendo 64",
        "region": "Europe",
        "size": 1234,
    }]}
    assert entries_from(payload)[0].path == "Nintendo 64/Europe/Mario Party.z64"


def test_walks_an_unexpected_wrapper_without_losing_the_tree():
    payload = {"response": {"directoryTree": {
        "type": "directory", "name": "NES", "children": [{
            "type": "file", "name": "Contra (USA).nes", "size": "4096"
        }]
    }}}
    entry = entries_from(payload)[0]
    assert (entry.path, entry.platform, entry.size_bytes) == (
        "NES/Contra (USA).nes", "nes", 4096
    )


def test_duplicate_paths_collapse():
    row = {"type": "file", "name": "Contra.nes", "path": "NES/Contra.nes", "size": 1}
    assert len(entries_from([row, dict(row)])) == 1


def test_download_url_quotes_each_path_segment():
    assert download_url(
        "Nintendo 64/Europe/Mario Party (Europe) (En,Fr,De).z64"
    ) == (
        "https://theromdepot.com/api/download/Nintendo%2064/Europe/"
        "Mario%20Party%20%28Europe%29%20%28En%2CFr%2CDe%29.z64"
    )


@pytest.mark.parametrize("bad", [
    "", "../secret", "NES/../../secret", "NES//Contra.nes",
    "https://evil.example/Contra.nes", "//evil.example/Contra.nes",
    "NES/Contra.nes?admin=1", "NES/Contra.nes#x", "C:/secret.rom",
    "NES/evil\nname.nes",
])
def test_unsafe_paths_are_rejected(bad):
    with pytest.raises(InvalidEntry):
        clean_path(bad)


def test_one_leading_root_slash_is_normalized():
    assert clean_path("/NES/Contra.nes") == "NES/Contra.nes"


@pytest.mark.parametrize("name,title", [
    ("Contra.nes", "Contra"),
    ("Game.7z", "Game"),
    ("README.txt", "README.txt"),
])
def test_display_title_only_removes_known_content_extensions(name, title):
    assert display_title(name) == title


def test_a_401_body_gives_an_actionable_catalogue_error(tmp_path):
    path = tmp_path / "signed-out.json"
    path.write_text(json.dumps({"message": "Unauthorized"}), encoding="utf-8")
    with pytest.raises(CatalogUnavailable, match="browser was logged in"):
        load_catalog(path)


def test_missing_configuration_names_the_browser_workflow():
    with pytest.raises(CatalogUnavailable, match="save https://theromdepot.com/api/getContents"):
        load_catalog("")


def test_invalid_json_is_reported_as_a_catalogue_error(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(CatalogUnavailable, match="cannot decode catalogue"):
        load_catalog(path)
