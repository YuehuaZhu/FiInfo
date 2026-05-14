import json
import logging
from pathlib import Path

from fiinfo.categorize import reclassify
from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.kol.ranker import top_n_by_category
from fiinfo.kol.seed_loader import load_seed_kols
from fiinfo.models import Kol, SignalRow, Tweet
from fiinfo.sources.base import TweetSource
from fiinfo.sources.fixture import FixtureTweetSource
from fiinfo.sources.playwright_src import PlaywrightTweetSource
from fiinfo.sources.registry import DEFAULT_CONFIG, load_sources

log = logging.getLogger(__name__)


def _make_source(name: str) -> TweetSource:
    if name == "fixture":
        return FixtureTweetSource()
    s = get_settings()
    return PlaywrightTweetSource(auth_token=s.twitter_auth_token, ct0=s.twitter_ct0)


def _upsert_kols(seed: list[Kol]) -> dict[str, int]:
    handle_to_id: dict[str, int] = {}
    with session_scope() as s:
        existing = {k.handle: k for k in s.query(Kol).all()}
        for k in seed:
            if k.handle in existing:
                e = existing[k.handle]
                e.display_name = k.display_name
                e.followers = k.followers
                e.category = k.category
                handle_to_id[k.handle] = e.id
            else:
                new = Kol(
                    handle=k.handle,
                    display_name=k.display_name,
                    followers=k.followers,
                    category=k.category,
                )
                s.add(new)
                s.flush()
                handle_to_id[k.handle] = new.id
    return handle_to_id


def collect_all(source_name: str | None = None) -> int:
    settings = get_settings()
    name = source_name or ("playwright" if settings.has_twitter_read else "fixture")
    src = _make_source(name)
    seed = load_seed_kols()
    top = top_n_by_category(seed, ratio=settings.top_kol_ratio)
    log.info("collecting from %d KOLs via %s", len(top), name)
    handle_to_id = _upsert_kols(seed)

    inserted = 0
    seen = 0
    try:
        with session_scope() as s:
            existing_ids = {row[0] for row in s.query(Tweet.tweet_id).all()}
            for k in top:
                for rt in src.fetch_recent(k.handle, limit=settings.daily_limit_per_category):
                    seen += 1
                    if rt.tweet_id in existing_ids:
                        continue
                    cat = reclassify(rt.text, default=k.category)
                    s.add(
                        Tweet(
                            kol_id=handle_to_id[rt.kol_handle],
                            tweet_id=rt.tweet_id,
                            url=rt.url,
                            text=rt.text,
                            lang=rt.lang,
                            posted_at=rt.posted_at,
                            likes=rt.likes,
                            retweets=rt.retweets,
                            replies=rt.replies,
                            category=cat,
                        )
                    )
                    existing_ids.add(rt.tweet_id)
                    inserted += 1
    finally:
        # 释放浏览器(Playwright 源会启动 chromium)
        close = getattr(src, "close", None)
        if callable(close):
            try:
                close()
            except Exception as e:
                log.warning("source close failed: %s", e)
    log.info("collected: %d new / %d total seen (%d dedup-skipped)",
             inserted, seen, seen - inserted)
    return inserted


def collect_signals(config_path: Path = DEFAULT_CONFIG) -> int:
    """新版多源采集:registry 加载 enabled sources,每个 source.fetch() → signals 表。

    返回新插入的 signal 数。
    """
    sources = load_sources(config_path)
    if not sources:
        log.warning("collect_signals: no enabled sources in %s", config_path)
        return 0

    inserted = 0
    total = 0
    with session_scope() as s:
        existing = {(r.source_kind, r.external_id) for r in s.query(
            SignalRow.source_kind, SignalRow.external_id).all()}
        for src in sources:
            kind = getattr(src, "kind", "?")
            name = getattr(src, "registry_name", type(src).__name__)
            try:
                sigs = src.fetch()
            except Exception as e:
                log.warning("source %s (%s) fetch failed: %s", name, kind, e)
                continue
            log.info("source %s (%s): %d signals", name, kind, len(sigs))
            for sig in sigs:
                total += 1
                key = (sig.source_kind, sig.external_id)
                if key in existing:
                    continue
                cat = reclassify(sig.text, default=sig.category)
                s.add(SignalRow(
                    source_kind=sig.source_kind,
                    source_name=sig.source_name,
                    external_id=sig.external_id,
                    url=sig.url,
                    title=sig.title or sig.text[:80],
                    text=sig.text,
                    lang=sig.lang,
                    author_handle=sig.author_handle,
                    posted_at=sig.posted_at,
                    score=sig.score,
                    raw_score_json=json.dumps(sig.raw_score, ensure_ascii=False),
                    category=cat,
                ))
                existing.add(key)
                inserted += 1
        # 调用源的 close (释放浏览器等)
        for src in sources:
            close = getattr(src, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as e:
                    log.warning("source close failed: %s", e)
    log.info("collect_signals: %d new / %d total (%d dup skipped)",
             inserted, total, total - inserted)
    return inserted
