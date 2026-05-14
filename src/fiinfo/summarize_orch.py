import datetime as dt
import logging

from fiinfo.categorize import top_per_category
from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.models import Summary, Tweet
from fiinfo.summarize.base import Summarizer
from fiinfo.summarize.echo import EchoSummarizer

log = logging.getLogger(__name__)


def _make_summarizer() -> Summarizer:
    settings = get_settings()
    if settings.has_llm:
        try:
            from fiinfo.summarize.claude import ClaudeSummarizer
            return ClaudeSummarizer()
        except Exception as e:
            log.warning("ClaudeSummarizer init failed (%s); falling back to Echo", e)
    return EchoSummarizer()


def summarize_today(force_mock: bool = False, today: str | None = None) -> int:
    today = today or dt.date.today().isoformat()
    summer: Summarizer = EchoSummarizer() if force_mock else _make_summarizer()
    count = 0
    with session_scope() as s:
        # 清掉今天已有的摘要,避免重跑重复
        s.query(Summary).filter(Summary.date == today).delete()
        all_tweets = s.query(Tweet).all()
        settings = get_settings()
        grouped = top_per_category(all_tweets, limit_per_cat=settings.daily_limit_per_category)
        for cat, tweets in grouped.items():
            md = summer.summarize_category(cat, tweets)
            tids = ",".join(t.tweet_id for t in tweets)
            s.add(Summary(date=today, category=cat, content_md=md, source_tweet_ids=tids))
            count += 1
    return count
