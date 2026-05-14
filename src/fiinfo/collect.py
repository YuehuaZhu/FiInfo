import logging

from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.kol.ranker import top_n_by_category
from fiinfo.kol.seed_loader import load_seed_kols
from fiinfo.models import Kol, Tweet
from fiinfo.sources.base import TweetSource
from fiinfo.sources.fixture import FixtureTweetSource
from fiinfo.sources.playwright_src import PlaywrightTweetSource

log = logging.getLogger(__name__)


def _make_source(name: str) -> TweetSource:
    if name == "fixture":
        return FixtureTweetSource()
    return PlaywrightTweetSource(auth_token=get_settings().twitter_auth_token)


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
    with session_scope() as s:
        existing_ids = {row[0] for row in s.query(Tweet.tweet_id).all()}
        for k in top:
            for rt in src.fetch_recent(k.handle, limit=settings.daily_limit_per_category):
                seen += 1
                if rt.tweet_id in existing_ids:
                    continue
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
                        category=k.category,
                    )
                )
                existing_ids.add(rt.tweet_id)
                inserted += 1
    log.info("collected: %d new / %d total seen (%d dedup-skipped)",
             inserted, seen, seen - inserted)
    return inserted
