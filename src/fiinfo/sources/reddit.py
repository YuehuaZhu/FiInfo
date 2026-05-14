"""Reddit hot posts via /r/<sub>/hot.rss (atom feed, 免认证)。

2024 后 Reddit JSON 端点封锁了未认证调用,但 .rss 端点仍开放。
我们用 feedparser 解析 atom feed,从 author / title / 时间提取信号。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import logging

import feedparser
import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"


def _parse_struct_time(st) -> dt.datetime:
    if not st:
        return dt.datetime.now(dt.UTC)
    try:
        return dt.datetime(*st[:6], tzinfo=dt.UTC)
    except Exception:
        return dt.datetime.now(dt.UTC)


def _short_id(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


class HotPostsSource:
    def __init__(self, subs: list[str] | None = None, limit_per_sub: int = 15):
        self.subs = subs or ["CryptoCurrency", "ethfinance", "ethereum", "solana", "defi"]
        self.limit_per_sub = limit_per_sub

    def fetch(self) -> list[Signal]:
        out: list[Signal] = []
        for sub in self.subs:
            out.extend(self._fetch_sub(sub))
        return out

    def _fetch_sub(self, sub: str) -> list[Signal]:
        url = f"https://www.reddit.com/r/{sub}/hot.rss?limit={self.limit_per_sub}"
        try:
            r = httpx.get(url, timeout=15.0, headers={"User-Agent": _UA},
                          follow_redirects=True)
            if r.status_code >= 400:
                log.warning("Reddit /r/%s returned %d", sub, r.status_code)
                todo_add(f"Reddit /r/{sub} 返回 {r.status_code}")
                return []
            feed = feedparser.parse(r.content)
        except Exception as e:
            log.warning("Reddit /r/%s failed: %s", sub, e)
            todo_add(f"Reddit /r/{sub} 失败: {type(e).__name__}")
            return []

        out: list[Signal] = []
        for entry in (feed.entries or [])[: self.limit_per_sub]:
            posted = _parse_struct_time(entry.get("updated_parsed") or entry.get("published_parsed"))
            title = (entry.get("title") or "").strip()
            link = entry.get("link") or ""
            author = (entry.get("author") or "anon").lstrip("/u/")
            ext = entry.get("id") or link
            content = ""
            if "content" in entry and entry.content:
                # atom content 是 HTML,粗暴去标签
                import re
                content = re.sub(r"<[^>]+>", " ", entry.content[0].get("value", ""))[:400].strip()
            text = f"r/{sub} · {title}" + (f"\n{content}" if content else "")
            out.append(Signal(
                source_kind="reddit",
                source_name=f"r/{sub}",
                external_id=f"reddit-{_short_id(ext)}",
                url=link,
                title=title,
                text=text,
                posted_at=posted,
                score=45.0,  # RSS 拿不到 ups,用统一中分,LLM 自己判断
                raw_score={"sub": sub, "author": author},
                category="",
                lang="en",
                author_handle=author,
            ))
        return out
