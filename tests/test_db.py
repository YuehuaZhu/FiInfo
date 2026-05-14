import datetime as dt

from fiinfo.db import init_db, session_scope
from fiinfo.models import Kol, Tweet


def test_can_insert_and_query():
    init_db()
    with session_scope() as s:
        k = Kol(handle="vitalik", display_name="Vitalik", followers=5_000_000, category="DeFi")
        s.add(k)
        s.flush()
        s.add(
            Tweet(
                kol_id=k.id,
                tweet_id="1",
                url="https://x.com/v/1",
                text="hello",
                lang="en",
                posted_at=dt.datetime.utcnow(),
                likes=10,
                retweets=2,
                replies=1,
                category="DeFi",
            )
        )
    with session_scope() as s:
        assert s.query(Tweet).count() == 1
        assert s.query(Kol).first().handle == "vitalik"
