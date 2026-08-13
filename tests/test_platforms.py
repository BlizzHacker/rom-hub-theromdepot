import pytest

from theromdepot.platforms import PLATFORM_ALIASES, normalise_label, platform_for

romarr_platforms = pytest.importorskip("romarr.platforms")


@pytest.mark.parametrize("alias,slug", sorted(PLATFORM_ALIASES.items()))
def test_every_mapped_slug_exists_in_romarr(alias, slug):
    resolved = romarr_platforms.resolve(slug)
    assert resolved is not None, f"{alias!r} maps to unknown platform {slug!r}"
    assert resolved.slug == slug


@pytest.mark.parametrize("label,slug", [
    ("Nintendo 64", "n64"),
    ("Super Nintendo Entertainment System", "snes"),
    ("Sony PlayStation 2", "ps2"),
    ("Sega Mega-Drive", "genesis-slash-megadrive"),
    ("NEC TurboGrafx-16", "turbografx16--1"),
])
def test_common_directory_labels_map_exactly(label, slug):
    assert platform_for(label) == slug


def test_unknown_and_ambiguous_labels_are_not_guessed():
    assert platform_for("Mystery Console") is None
    assert platform_for("Neo Geo") is None


def test_normalisation_only_changes_punctuation_spacing_and_case():
    assert normalise_label("  Nintendo_64 ") == "nintendo 64"
