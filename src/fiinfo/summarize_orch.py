import datetime as dt
import logging

from sqlalchemy.orm import joinedload

from fiinfo.categorize import top_per_category, top_signals_per_category
from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.models import SignalRow, Summary, Tweet
from fiinfo.summarize.base import Summarizer
from fiinfo.summarize.echo import EchoSummarizer

log = logging.getLogger(__name__)


def _make_summarizer() -> Summarizer:
    """优先级:千问(阿里) → 豆包(火山方舟) → Claude → Echo mock。"""
    settings = get_settings()
    if settings.has_qwen:
        try:
            from fiinfo.summarize.qwen import QwenSummarizer
            log.info("summarizer: Qwen (%s)", settings.dashscope_model)
            return QwenSummarizer()
        except Exception as e:
            log.warning("QwenSummarizer init failed (%s); trying Doubao next", e)
    if settings.has_doubao:
        try:
            from fiinfo.summarize.doubao import DoubaoSummarizer
            log.info("summarizer: Doubao (%s)", settings.ark_model)
            return DoubaoSummarizer()
        except Exception as e:
            log.warning("DoubaoSummarizer init failed (%s); trying Claude next", e)
    if settings.has_claude:
        try:
            from fiinfo.summarize.claude import ClaudeSummarizer
            log.info("summarizer: Claude (%s)", settings.anthropic_model)
            return ClaudeSummarizer()
        except Exception as e:
            log.warning("ClaudeSummarizer init failed (%s); falling back to Echo", e)
    log.info("summarizer: Echo (no LLM credentials)")
    return EchoSummarizer()


def summarize_today(force_mock: bool = False, today: str | None = None) -> int:
    today = today or dt.date.today().isoformat()
    summer: Summarizer = EchoSummarizer() if force_mock else _make_summarizer()
    count = 0
    with session_scope() as s:
        # 清掉今天已有的摘要,避免重跑重复
        s.query(Summary).filter(Summary.date == today).delete()
        all_tweets = s.query(Tweet).options(joinedload(Tweet.kol)).all()
        settings = get_settings()
        grouped = top_per_category(all_tweets, limit_per_cat=settings.daily_limit_per_category)
        for cat, tweets in grouped.items():
            md = summer.summarize_category(cat, tweets)
            tids = ",".join(t.tweet_id for t in tweets)
            s.add(Summary(date=today, category=cat, content_md=md, source_tweet_ids=tids))
            count += 1
    return count


_CHAN_PREFIX = "__chan:"  # Summary.category 用此前缀标识"按渠道"摘要,以区分按类目


def summarize_channels_today(force_mock: bool = False, today: str | None = None,
                              top_per_channel: int = 25) -> int:
    """按 source_kind 分组,对每个渠道生成中文摘要。

    写入 Summary 表,category 形如 `__chan:twitter`,以避免与按类目摘要冲突。
    """
    today = today or dt.date.today().isoformat()
    summer: Summarizer = EchoSummarizer() if force_mock else _make_summarizer()
    count = 0
    with session_scope() as s:
        # 清旧的渠道摘要
        s.query(Summary).filter(
            Summary.date == today,
            Summary.category.like(f"{_CHAN_PREFIX}%"),
        ).delete(synchronize_session=False)

        all_signals = s.query(SignalRow).all()
        # 按 source_kind 分组并按 score 排序
        buckets: dict[str, list] = {}
        for sig in all_signals:
            buckets.setdefault(sig.source_kind, []).append(sig)
        for kind, sigs in buckets.items():
            sigs.sort(key=lambda x: x.score, reverse=True)
            top = sigs[:top_per_channel]
            md = summer.summarize_category(f"{kind} 渠道", top)
            ids = ",".join(f"{x.source_kind}:{x.external_id}" for x in top)
            s.add(Summary(date=today, category=f"{_CHAN_PREFIX}{kind}",
                          content_md=md, source_signal_ids=ids))
            count += 1
    return count


def summarize_today_from_signals(force_mock: bool = False, today: str | None = None) -> int:
    """新版:从 signals 表读 + 按 score 排序 + 按类目摘要。

    与 summarize_today 并存(legacy 通过 tweets 表),最终目标是只保留这个。
    """
    today = today or dt.date.today().isoformat()
    summer: Summarizer = EchoSummarizer() if force_mock else _make_summarizer()
    count = 0
    with session_scope() as s:
        # 只清按类目摘要(不带 __chan: 前缀的),保留渠道摘要不动
        s.query(Summary).filter(
            Summary.date == today,
            ~Summary.category.like(f"{_CHAN_PREFIX}%"),
        ).delete(synchronize_session=False)
        all_signals = s.query(SignalRow).all()
        settings = get_settings()
        grouped = top_signals_per_category(
            all_signals, limit_per_cat=settings.daily_limit_per_category
        )
        for cat, sigs in grouped.items():
            md = summer.summarize_category(cat, sigs)
            ids = ",".join(f"{x.source_kind}:{x.external_id}" for x in sigs)
            s.add(Summary(date=today, category=cat, content_md=md, source_signal_ids=ids))
            count += 1
    return count
