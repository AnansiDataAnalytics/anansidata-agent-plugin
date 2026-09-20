from anansi_mcp.resolve import (
    region_country_names,
    region_for_country,
    resolve_countries,
    resolve_country,
)


def test_resolves_common_names_and_codes_to_canonical_names():
    assert resolve_country("India") == "India"
    assert resolve_country("IND") == "India"
    assert resolve_country("United States") == "United States of America (the)"
    assert resolve_country("USA") == "United States of America (the)"
    assert resolve_country("US") == "United States of America (the)"
    assert (
        resolve_country("UK")
        == "United Kingdom of Great Britain and Northern Ireland (the)"
    )
    assert resolve_country("South Korea") == "Korea (the Republic of)"
    assert resolve_country("Russia") == "Russian Federation (the)"


def test_unresolved_is_reported_not_guessed():
    assert resolve_country("Wakanda") is None
    resolved, missing = resolve_countries(["India", "Wakanda"])
    assert resolved == ["India"]
    assert missing == ["Wakanda"]


def test_region_lookup():
    assert region_for_country("India") == "Asia"
    assert region_for_country("Nigeria") == "Africa"
    assert "Australia" in region_country_names("Oceania")
    assert region_country_names("Atlantis") == []
