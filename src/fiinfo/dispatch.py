import datetime as dt
import logging
from pathlib import Path

from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.models import DispatchLog, Summary
from fiinfo.publish.base import Publisher
from fiinfo.publish.dryrun import DryRunPublisher

log = logging.getLogger(__name__)


def _summary_to_thread(category: str, md: str) -> list[str]:
    body = [ln.strip("- ").strip() for ln in md.splitlines() if ln.strip().startswith("- ")][:4]
    if not body:
        body = [md[:240]]
    head = f"🧵 #{category} 今日要点 ({dt.date.today().isoformat()})"
    return [head] + [b[:270] for b in body]


def _make_publisher(dry_run: bool, outbox: Path | None = None) -> Publisher:
    settings = get_settings()
    if dry_run or not settings.has_twitter_write:
        return DryRunPublisher(outbox=outbox or (settings.data_dir / "outbox"))
    from fiinfo.publish.twitter import TwitterPublisher

    return TwitterPublisher(
        consumer_key=settings.twitter_write_consumer_key,
        consumer_secret=settings.twitter_write_consumer_secret,
        access_token=settings.twitter_write_access_token,
        access_secret=settings.twitter_write_access_secret,
    )


def dispatch_today(dry_run: bool = True, outbox: Path | None = None, today: str | None = None) -> int:
    today = today or dt.date.today().isoformat()
    pub = _make_publisher(dry_run=dry_run, outbox=outbox)
    with session_scope() as s:
        summaries = s.query(Summary).filter(Summary.date == today).all()
        threads = [_summary_to_thread(sm.category, sm.content_md) for sm in summaries]
        cats = [sm.category for sm in summaries]
    if not threads:
        log.warning("no summaries found for %s, skipping dispatch", today)
        return 0
    ids = pub.publish_threads(threads)
    with session_scope() as s:
        for cat, tid in zip(cats, ids, strict=False):
            s.add(
                DispatchLog(
                    date=today,
                    channel="twitter",
                    status="dry" if dry_run else "ok",
                    payload=f"{cat}:{tid}",
                )
            )
    return len(ids)
