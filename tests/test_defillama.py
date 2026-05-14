from unittest.mock import patch

from fiinfo.sources.defillama import HacksSource, RaisesSource, TVLSource, _map_category


def test_category_mapping():
    assert _map_category("Dexs") == "DEXAMM"
    assert _map_category("Liquid Restaking") == "Restaking"
    assert _map_category("RWA") == "RWA"
    assert _map_category("Derivatives") == "PerpDEX"
    assert _map_category(None) == ""
    assert _map_category("Some Random Thing") == ""


def test_tvl_parses_response():
    fake = [
        {"name": "Hyperliquid", "slug": "hyperliquid", "tvl": 5_000_000_000,
         "change_1d": 8.5, "category": "Derivatives", "chains": ["Hyperliquid"]},
        {"name": "Ondo Finance", "slug": "ondo-finance", "tvl": 2_000_000_000,
         "change_1d": -4.2, "category": "RWA", "chains": ["Ethereum"]},
        {"name": "Tiny", "slug": "tiny", "tvl": 100, "change_1d": 99,
         "category": "Dexs", "chains": ["Ethereum"]},  # 应被 tvl 阈值过滤
    ]
    with patch("fiinfo.sources.defillama._http_get_json", return_value=fake):
        sigs = TVLSource(top_n=10, min_change_pct=3.0).fetch()
    assert len(sigs) == 2
    cats = {s.category for s in sigs}
    assert "PerpDEX" in cats and "RWA" in cats
    # source_kind 与 url 正确
    assert all(s.source_kind == "defillama_tvl" for s in sigs)
    assert all("defillama.com/protocol/" in s.url for s in sigs)


def test_raises_402_returns_empty():
    """付费端点 silent 跳过,不报错。"""
    with patch("fiinfo.sources.defillama._http_get_json", return_value=None):
        assert RaisesSource().fetch() == []


def test_hacks_parses_response():
    import datetime as dt
    recent_ts = int(dt.datetime.now(dt.UTC).timestamp())
    fake = [
        {"name": "X Protocol", "amount": 500_000, "date": recent_ts,
         "technique": "Reentrancy", "classification": "Protocol Logic",
         "chain": "Ethereum", "source": "https://example.com/x"},
    ]
    with patch("fiinfo.sources.defillama._http_get_json", return_value=fake):
        sigs = HacksSource(since_days=30).fetch()
    assert len(sigs) == 1
    assert sigs[0].source_kind == "defillama_hacks"
    assert "X Protocol" in sigs[0].text
