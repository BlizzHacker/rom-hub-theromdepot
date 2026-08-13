import pytest

from rom_hub_sdk import PluginContext, SearchResult

from conftest import NoHttp
from theromdepot.search import Search
from theromdepot.stream import Stream, StreamRefused


def context(catalog_path):
    return PluginContext(config={"catalog_path": str(catalog_path)}, http=NoHttp())


def test_search_uses_the_whole_captured_tree_without_network(catalog_path):
    results = Search(context(catalog_path)).search("mario party", None, 20)
    assert len(results) == 1
    result = results[0]
    assert result.title == "Mario Party (Europe) (En,Fr,De)"
    assert result.platform == "n64"
    assert result.size_bytes == 1234
    assert result.source_id == "Nintendo 64/Europe/Mario Party (Europe) (En,Fr,De).z64"


def test_search_marks_the_browser_login_contract(catalog_path):
    result = Search(context(catalog_path)).search("mario", None, 1)[0]
    assert result.url.startswith("https://theromdepot.com/api/download/")
    assert result.extra["login_required"] == "true"
    assert result.extra["browser_authenticated"] == "true"
    assert result.extra["action"] == "download"
    assert result.extra["catalogue_source"] == "/api/getContents"
    assert result.extra["playable"] == "false"


@pytest.mark.parametrize("spelling", ["n64", "Nintendo 64", "nintendo_64"])
def test_platform_filter_accepts_canonical_and_site_spellings(catalog_path, spelling):
    results = Search(context(catalog_path)).search("legend", spelling, 20)
    assert [result.platform for result in results] == ["n64"]


def test_platform_filter_excludes_other_systems(catalog_path):
    assert Search(context(catalog_path)).search("contra", "n64", 20) == []


def test_search_matches_region_and_path_metadata(catalog_path):
    assert Search(context(catalog_path)).search("europe mario", None, 20)[0].platform == "n64"


def test_search_honours_limit(catalog_path):
    assert len(Search(context(catalog_path)).search("usa", None, 1)) == 1


def test_empty_query_and_zero_limit_do_not_even_read_the_catalogue():
    ctx = PluginContext(config={}, http=NoHttp())
    assert Search(ctx).search("  ", None, 20) == []
    assert Search(ctx).search("mario", None, 0) == []


def test_stream_hands_the_authenticated_download_to_the_operators_browser(catalog_path):
    result = Search(context(catalog_path)).search("mario", None, 1)[0]
    target = Stream(context(catalog_path)).resolve(result)
    assert target.kind == "url"
    assert target.target == result.url
    assert target.mime_type == "application/octet-stream"
    assert target.extra["login_required"] == "true"
    assert target.extra["action"] == "download"


def test_stream_revalidates_membership_in_the_captured_tree(catalog_path):
    invented = SearchResult(source_id="NES/Invented.nes", title="Invented", platform="nes")
    with pytest.raises(StreamRefused, match="not a file"):
        Stream(context(catalog_path)).resolve(invented)


@pytest.mark.parametrize("bad", [
    "../secret", "https://evil.example/file", "NES/../../secret", "NES/file#x",
])
def test_stream_rejects_unsafe_round_tripped_ids(catalog_path, bad):
    result = SearchResult(source_id=bad, title="bad")
    with pytest.raises(StreamRefused, match="invalid The ROM Depot path"):
        Stream(context(catalog_path)).resolve(result)


def test_no_importer_is_advertised_because_the_host_has_no_browser_cookie():
    import theromdepot

    assert not hasattr(theromdepot, "importer")
