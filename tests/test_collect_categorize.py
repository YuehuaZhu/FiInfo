import datetime as dt

from fiinfo.categorize import top_per_category
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
        assert {"DeFi", "AIAgent"}.issubset(cats)


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


def test_top_per_category_limit_and_order():
    tweets = [_t("DeFi", i, f"d{i}") for i in range(50)] + [_t("AIAgent", i, f"a{i}") for i in range(10)]
    grouped = top_per_category(tweets, limit_per_cat=30)
    assert len(grouped["DeFi"]) == 30
    assert grouped["DeFi"][0].likes >= grouped["DeFi"][-1].likes
    assert len(grouped["AIAgent"]) == 10
