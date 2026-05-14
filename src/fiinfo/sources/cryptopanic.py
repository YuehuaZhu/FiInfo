"""CryptoPanic 新闻聚合(支持 API key,缺 key 退到 RSS)。"""
from __future__ import annotations

import datetime as dt
import logging
import os

import feedparser
import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_API = "https://cryptopanic.com/api/v1/posts/"
_RSS = "https://cryptopanic.com/news/rss/"


class NewsSource:
    """优先用 API(配 CRYPTOPANIC_TOKEN);否则降级 RSS。"""

    def __init__(self, filter: str = "hot", limit: int = 50):
        self.filter = filter
        self.limit = limit
        self.token = os.getenv("CRYPTOPANIC_TOKEN", "")

    def fetch(self) -> list[Signal]:
        if self.token:
            return self._fetch_api()
        return self._fetch_rss()

    def _fetch_api(self) -> list[Signal]:
        try:
            r = httpx.get(_API, timeout=20.0,
                          params={"auth_token": self.token, "filter": self.filter},
                          headers={"User-Agent": "fiinfo/0.1"})
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning("CryptoPanic API failed (%s); falling back to RSS", e)
            return self._fetch_rss()

        out: list[Signal] = []
        for it in (data.get("results") or [])[: self.limit]:
            title = it.get("title", "")
            pub = it.get("published_at") or it.get("created_at")
            try:
                posted = dt.datetime.fromisoformat((pub or "").replace("Z", "+00:00"))
            except Exception:
                posted = dt.datetime.now(dt.UTC)
            votes = it.get("votes") or {}
            score_raw = (votes.get("positive", 0) - votes.get("negative", 0)
                         + votes.get("important", 0) * 2)
            out.append(Signal(
                source_kind="cryptopanic",
                source_name=(it.get("source") or {}).get("title", "cryptopanic"),
                external_id=f"cp-{it.get('id')}",
                url=it.get("url") or _RSS,
                title=title,
                text=title,
                posted_at=posted,
                score=min(100.0, 30.0 + score_raw * 5),
                raw_score=votes,
                category="",
                lang="en",
                author_handle="cryptopanic",
            ))
        return out

    def _fetch_rss(self) -> list[Signal]:
        try:
            feed = feedparser.parse(_RSS)
        except Exception as e:
            log.warning("CryptoPanic RSS failed: %s", e)
            todo_add(f"CryptoPanic RSS 失败: {type(e).__name__}: {e}")
            return []
        out: list[Signal] = []
        for entry in (feed.entries or [])[: self.limit]:
            posted = _parse_struct_time(entry.get("published_parsed"))
            title = entry.get("title", "")
            link = entry.get("link", _RSS)
            ext_id = entry.get("id") or link
            out.append(Signal(
                source_kind="cryptopanic",
                source_name="cryptopanic-rss",
                external_id=f"cp-rss-{abs(hash(ext_id))}",
                url=link,
                title=title,
                text=title + " — " + (entry.get("summary", "") or "")[:300],
                posted_at=posted,
                score=40.0,
                raw_score={"feed": "rss"},
                category="",
                lang="en",
                author_handle="cryptopanic",
            ))
        return out


def _parse_struct_time(st) -> dt.datetime:
    if not st:
        return dt.datetime.now(dt.UTC)
    try:
        return dt.datetime(*st[:6], tzinfo=dt.UTC)
    except Exception:
        return dt.datetime.now(dt.UTC)
