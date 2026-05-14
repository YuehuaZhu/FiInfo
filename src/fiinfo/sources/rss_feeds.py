"""通用 RSS 聚合 source。从 config 里读 feed URL 列表。

支持中英文媒体:Cointelegraph / The Block / Decrypt / Foresight / ChainCatcher / Odaily 等。
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

# 浏览器风 UA,避开简单的 403 拦截
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _parse_struct_time(st) -> dt.datetime:
    if not st:
        return dt.datetime.now(dt.UTC)
    try:
        return dt.datetime(*st[:6], tzinfo=dt.UTC)
    except Exception:
        return dt.datetime.now(dt.UTC)


def _short_id(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()[:16]


def _detect_lang(text: str) -> str:
    """粗判中英 —— 中文字符占比 > 20% 就视作 zh。"""
    if not text:
        return "en"
    cn = sum(1 for c in text if "一" <= c <= "鿿")
    return "zh" if cn / max(len(text), 1) > 0.2 else "en"


class RSSSource:
    """读一组 RSS feed,合并产出 Signal。"""

    def __init__(self, feeds: list[str] | None = None, limit_per_feed: int = 15):
        self.feeds = feeds or []
        self.limit_per_feed = limit_per_feed

    def fetch(self) -> list[Signal]:
        out: list[Signal] = []
        for url in self.feeds:
            sigs = self._fetch_one(url)
            log.info("RSS %s: %d items", url, len(sigs))
            out.extend(sigs)
        return out

    def _fetch_one(self, url: str) -> list[Signal]:
        try:
            r = httpx.get(url, timeout=20.0,
                          headers={"User-Agent": _UA, "Accept": "application/rss+xml, application/xml, text/xml"},
                          follow_redirects=True)
            if r.status_code >= 400:
                log.warning("RSS %s returned %d", url, r.status_code)
                todo_add(f"RSS {url} 返回 {r.status_code}(可能需要 UA / 反爬)")
                return []
            feed = feedparser.parse(r.content)
        except Exception as e:
            log.warning("RSS %s failed: %s", url, e)
            todo_add(f"RSS {url} 失败: {type(e).__name__}")
            return []

        source_name = (feed.feed.get("title", "") or url.split("//")[-1].split("/")[0]).strip()
        out: list[Signal] = []
        for entry in (feed.entries or [])[: self.limit_per_feed]:
            posted = _parse_struct_time(entry.get("published_parsed") or entry.get("updated_parsed"))
            title = (entry.get("title") or "").strip()
            link = entry.get("link") or url
            summary = (entry.get("summary") or "")[:500].strip()
            text = f"{title}{' — ' + summary if summary else ''}"
            ext = entry.get("id") or link
            out.append(Signal(
                source_kind="rss",
                source_name=source_name,
                external_id=f"rss-{_short_id(ext)}",
                url=link,
                title=title,
                text=text,
                posted_at=posted,
                score=50.0,  # RSS 无热度信号,统一中分
                raw_score={"feed": url},
                category="",  # reclassify 走关键词
                lang=_detect_lang(title + summary),
                author_handle=source_name,
            ))
        return out
