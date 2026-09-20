from anansi_mcp.tools._shared import partition_countries


def test_partition_countries_splits_comma_names():
    plain, comma = partition_countries(
        ["India", "Bonaire, Sint Eustatius and Saba", "Tanzania, United Republic of"]
    )
    assert plain == ["India"]
    assert comma == [
        "Bonaire, Sint Eustatius and Saba",
        "Tanzania, United Republic of",
    ]


def test_partition_countries_all_plain():
    plain, comma = partition_countries(["India", "United States of America (the)"])
    assert plain == ["India", "United States of America (the)"]
    assert comma == []
