import datetime as dt
from unittest.mock import MagicMock

from fiinfo.collect import collect_all
from fiinfo.db import init_db, session_scope
from fiinfo.models import Summary, Tweet
from fiinfo.summarize.claude import ClaudeSummarizer
from fiinfo.summarize.echo import EchoSummarizer
from fiinfo.summarize_orch import summarize_today


def _t(text, tid):
    return Tweet(
        tweet_id=tid,
        url=f"https://x.com/u/{tid}",
        text=text,
        lang="en",
        posted_at=dt.datetime.now(dt.UTC),
        likes=10,
        retweets=1,
        replies=0,
        category="DeFi",
        kol_id=1,
    )


def test_echo_includes_category_and_citations():
    out = EchoSummarizer().summarize_category("DeFi", [_t("ZK rollups are hot", "z1"), _t("Vitalik blog", "z2")])
    assert "DeFi" in out
    assert "z1" in out and "z2" in out


def test_echo_empty_returns_no_tweets_today():
    assert "no tweets" in EchoSummarizer().summarize_category("DeFi", [])


def test_claude_summarizer_uses_injected_client():
    fake = MagicMock()
    fake.messages.create.return_value = MagicMock(content=[MagicMock(text="## DeFi\n- summary")])
    s = ClaudeSummarizer(client=fake, model="claude-sonnet-4-6")
    md = s.summarize_category("DeFi", [_t("hi", "x1")])
    assert "DeFi" in md
    fake.messages.create.assert_called_once()


def test_summarize_today_writes_rows():
    init_db()
    collect_all(source_name="fixture")
    n = summarize_today(force_mock=True)
    assert n >= 1
    with session_scope() as s:
        cats = {r.category for r in s.query(Summary).all()}
        # fixture 通过 reclassify 至少会落在 ≥2 个新类目里
        assert len(cats) >= 2
