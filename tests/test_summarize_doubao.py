import datetime as dt
from unittest.mock import MagicMock

from fiinfo.models import Tweet
from fiinfo.summarize.doubao import DoubaoSummarizer


def _t(text, tid):
    return Tweet(
        tweet_id=tid, url=f"https://x.com/u/{tid}", text=text, lang="en",
        posted_at=dt.datetime.now(dt.UTC), likes=10, retweets=1, replies=0,
        category="PerpDEX", kol_id=1,
    )


def test_doubao_calls_chat_completions():
    fake = MagicMock()
    fake.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="## PerpDEX\n- summary line"))]
    )
    s = DoubaoSummarizer(client=fake, model="doubao-pro-32k")
    out = s.summarize_category("PerpDEX", [_t("hi", "x1")])
    assert "PerpDEX" in out
    fake.chat.completions.create.assert_called_once()
    kwargs = fake.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "doubao-pro-32k"
    assert kwargs["messages"][0]["role"] == "user"


def test_doubao_empty_tweets_returns_placeholder():
    fake = MagicMock()
    s = DoubaoSummarizer(client=fake, model="doubao-pro-32k")
    out = s.summarize_category("PerpDEX", [])
    assert "no tweets" in out
    fake.chat.completions.create.assert_not_called()
