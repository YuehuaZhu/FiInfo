"""Reddit hot posts from crypto subs (JSON API,无需 token)。"""
from __future__ import annotations

import datetime as dt
import logging

import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_UA = "fiinfo/0.1 (by /u/fiinfo)"


class HotPostsSource:
    def __init__(self, subs: list[str] | None = None, limit_per_sub: int = 15):
        self.subs = subs or ["CryptoCurrency", "ethfinance", "solana", "defi"]
        self.limit_per_sub = limit_per_sub

    def fetch(self) -> list[Signal]:
        out: list[Signal] = []
        for sub in self.subs:
            out.extend(self._fetch_sub(sub))
        return out

    def _fetch_sub(self, sub: str) -> list[Signal]:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit={self.limit_per_sub}"
        try:
            r = httpx.get(url, timeout=20.0, headers={"User-Agent": _UA},
                          follow_redirects=True)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning("Reddit /r/%s failed: %s", sub, e)
            todo_add(f"Reddit /r/{sub} 失败: {type(e).__name__}")
            return []

        out: list[Signal] = []
        for child in (data.get("data") or {}).get("children") or []:
            d = child.get("data") or {}
            if d.get("stickied") or d.get("over_18"):
                continue
            posted = dt.datetime.fromtimestamp(int(d.get("created_utc") or 0), tz=dt.UTC)
            title = d.get("title", "")
            url_post = d.get("url") or f"https://reddit.com{d.get('permalink', '')}"
            ups = int(d.get("ups") or 0)
            comments = int(d.get("num_comments") or 0)
            selftext = (d.get("selftext") or "")[:400]
            text = f"r/{sub} · {title}" + (f"\n{selftext}" if selftext else "")
            out.append(Signal(
                source_kind="reddit",
                source_name=f"r/{sub}",
                external_id=f"reddit-{d.get('id')}",
                url=f"https://reddit.com{d.get('permalink')}" if d.get("permalink") else url_post,
                title=title,
                text=text,
                posted_at=posted,
                score=min(100.0, 25.0 + ups / 100),
                raw_score={"ups": ups, "comments": comments},
                category="",
                lang="en",
                author_handle=d.get("author") or "reddit",
            ))
        return out
