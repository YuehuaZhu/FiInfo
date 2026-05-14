import datetime as dt

from fiinfo.categorize import reclassify, top_per_category
from fiinfo.collect import collect_all
from fiinfo.db import init_db, session_scope
from fiinfo.models import Tweet


def test_collect_inserts_from_fixture():
    init_db()
    n = collect_all(source_name="fixture")
    assert n > 0
    with session_scope() as s:
        rows = s.query(Tweet).all()
        assert len(rows) == n
        cats = {r.category for r in rows}
        # 至少 2 个不同类目(关键词覆写应该让 cz_binance 的 Hyperliquid 推文跑到 PerpDEX)
        assert len(cats) >= 2
        assert "PerpDEX" in cats or "Restaking" in cats


def _t(cat, likes, tid):
    return Tweet(
        tweet_id=tid,
        url="",
        text="x",
        lang="en",
        posted_at=dt.datetime.now(dt.UTC),
        likes=likes,
        retweets=0,
        replies=0,
        category=cat,
        kol_id=1,
    )


def test_reclassify_overrides_by_keyword():
    # Hyperliquid → PerpDEX 不论默认类目是什么
    assert reclassify("Hyperliquid HIP-3 is wild", default="DEXAMM") == "PerpDEX"
    # 没命中关键词时返回 default
    assert reclassify("just some random thoughts today", default="InfraL2") == "InfraL2"
    # USDC 关键词 → Stablecoin
    assert reclassify("USDC mints surged this week", default="DEXAMM") == "Stablecoin"
    # 空字符串
    assert reclassify("", default="Wallet") == "Wallet"


def test_top_per_category_limit_and_order():
    tweets = [_t("DeFi", i, f"d{i}") for i in range(50)] + [_t("AIAgent", i, f"a{i}") for i in range(10)]
    grouped = top_per_category(tweets, limit_per_cat=30)
    assert len(grouped["DeFi"]) == 30
    assert grouped["DeFi"][0].likes >= grouped["DeFi"][-1].likes
    assert len(grouped["AIAgent"]) == 10
