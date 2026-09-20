from anansi_mcp import compute

OBS = [
    {"date": "2020-01-01", "value": 100.0, "is_forecast": False},
    {"date": "2021-01-01", "value": 110.0, "is_forecast": False},
    {"date": "2022-01-01", "value": 121.0, "is_forecast": False},
]


def test_growth_is_percent_change():
    result = compute.growth(OBS)
    assert [round(r["value"], 1) for r in result] == [10.0, 10.0]


def test_cagr():
    result = compute.cagr(OBS)
    assert result["years"] == 2
    assert round(result["cagr_pct"], 1) == 10.0


def test_rebase_starts_at_100():
    result = compute.rebase(OBS)
    assert result[0]["value"] == 100.0
    assert round(result[-1]["value"], 1) == 121.0


def test_correlation_of_identical_series_is_one():
    result = compute.correlation(OBS, OBS)
    assert result["correlation"] == 1.0


def test_spread_aligns_on_common_dates():
    other = [
        {"date": "2020-01-01", "value": 40.0},
        {"date": "2021-01-01", "value": 50.0},
        {"date": "2022-01-01", "value": 60.0},
    ]
    result = compute.spread(OBS, other)
    assert [r["value"] for r in result] == [60.0, 60.0, 61.0]
