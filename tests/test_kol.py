from fiinfo.kol.ranker import top_n_by_category
from fiinfo.kol.seed_loader import load_seed_kols
from fiinfo.models import Kol


def test_seed_loads_at_least_25():
    kols = load_seed_kols()
    assert len(kols) >= 25
    assert {"DeFi", "AIAgent", "Ecommerce", "Staking"} <= {k.category for k in kols}


def _mk(handle, cat, followers):
    return Kol(handle=handle, category=cat, followers=followers)


def test_top_n_ratio_per_category():
    kols = [_mk(f"u{i}", "DeFi", i * 1000) for i in range(1, 11)]
    top = top_n_by_category(kols, ratio=0.3)
    assert {k.handle for k in top} == {"u10", "u9", "u8"}


def test_top_n_multi_category_min_one():
    kols = [_mk("a", "DeFi", 10), _mk("b", "DeFi", 20), _mk("c", "AIAgent", 5)]
    top = top_n_by_category(kols, ratio=0.5)
    handles = {k.handle for k in top}
    assert "b" in handles and "c" in handles
