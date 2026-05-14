import datetime as dt
from unittest.mock import MagicMock

from fiinfo.models import Tweet
from fiinfo.summarize.qwen import QwenSummarizer


def _t(text, tid):
    return Tweet(
        tweet_id=tid, url=f"https://x.com/u/{tid}", text=text, lang="en",
        posted_at=dt.datetime.now(dt.UTC), likes=10, retweets=1, replies=0,
        category="PerpDEX", kol_id=1,
    )


def test_qwen_calls_chat_completions():
    fake = MagicMock()
    fake.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="## PerpDEX\n- summary"))]
    )
    s = QwenSummarizer(client=fake, model="qwen-max")
    out = s.summarize_category("PerpDEX", [_t("hi", "x1")])
    assert "PerpDEX" in out
    kwargs = fake.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "qwen-max"


def test_qwen_empty_returns_placeholder():
    fake = MagicMock()
    s = QwenSummarizer(client=fake, model="qwen-max")
    assert "no tweets" in s.summarize_category("PerpDEX", [])
    fake.chat.completions.create.assert_not_called()
