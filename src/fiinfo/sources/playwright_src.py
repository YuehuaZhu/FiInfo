"""Twitter/X 抓取 — 注入 cookie + 解析 DOM。

设计:
- 单浏览器实例复用,KOL 间随机 5-10s 间隔降低风控
- 只取原创推文,跳过转推与置顶
- 数字解析支持 "1.2K" / "5.4M" 这种缩写
- DOM 取不到时 log warning 并跳过该 KOL,不抛异常打断流水线
"""
from __future__ import annotations

import datetime as dt
import logging
import random
import re
import time

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base import RawTweet, TweetSource
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_TWEET_ID_RE = re.compile(r"/status/(\d+)")
_NUM_RE = re.compile(r"^([\d.]+)([KMB]?)$", re.IGNORECASE)


def _parse_count(s: str | None) -> int:
    """'1.2K' -> 1200; '5.4M' -> 5400000; '' -> 0"""
    if not s:
        return 0
    s = s.strip().replace(",", "")
    if s.isdigit():
        return int(s)
    m = _NUM_RE.match(s)
    if not m:
        return 0
    num = float(m.group(1))
    unit = m.group(2).upper()
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(unit, 1)
    return int(num * mult)


class PlaywrightTweetSource(TweetSource):
    """通过登录态 cookie + Playwright 抓取公开 KOL 推文。"""

    def __init__(self, auth_token: str = "", ct0: str = "", headless: bool = True):
        self.auth_token = auth_token
        self.ct0 = ct0
        self.headless = headless
        self._browser = None
        self._context = None
        self._playwright = None
        if not auth_token:
            todo_add("配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取")

    def _ensure_browser(self):
        if self._browser is not None:
            return
        from playwright.sync_api import sync_playwright

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(user_agent=_UA, viewport={"width": 1280, "height": 900})
        cookies = [
            {"name": "auth_token", "value": self.auth_token, "domain": ".x.com",
             "path": "/", "secure": True, "httpOnly": True, "sameSite": "None"},
        ]
        if self.ct0:
            cookies.append({"name": "ct0", "value": self.ct0, "domain": ".x.com",
                            "path": "/", "secure": True, "httpOnly": False, "sameSite": "Lax"})
        self._context.add_cookies(cookies)

    def close(self):
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            log.warning("close failed: %s", e)
        finally:
            self._context = self._browser = self._playwright = None

    def __del__(self):
        self.close()

    def fetch_recent(self, handle: str, limit: int = 30) -> list[RawTweet]:
        if not self.auth_token:
            log.warning("PlaywrightTweetSource: no cookie, skipping %s", handle)
            return []
        try:
            self._ensure_browser()
            return self._fetch_one(handle, limit)
        except Exception as e:
            log.warning("fetch %s failed: %s", handle, e)
            todo_add(f"Playwright 抓取 @{handle} 失败: {type(e).__name__}: {e}")
            return []

    def _fetch_one(self, handle: str, limit: int) -> list[RawTweet]:
        page = self._context.new_page()
        try:
            url = f"https://x.com/{handle}"
            log.info("fetching %s", url)
            page.goto(url, wait_until="load", timeout=45_000)
            try:
                page.wait_for_selector('article[data-testid="tweet"]', timeout=20_000)
                page.wait_for_timeout(2000)  # 让更多 tweet 完成渲染
            except Exception:
                log.warning("@%s: no tweets rendered (页面可能未登录或 KOL 不存在)", handle)
                return []

            collected: dict[str, RawTweet] = {}
            stagnant_rounds = 0
            for _ in range(6):  # 最多滚 6 次
                articles = page.query_selector_all('article[data-testid="tweet"]')
                before = len(collected)
                for art in articles:
                    rt = self._parse_article(art, handle)
                    if rt and rt.tweet_id not in collected:
                        collected[rt.tweet_id] = rt
                        if len(collected) >= limit:
                            break
                if len(collected) >= limit:
                    break
                if len(collected) == before:
                    stagnant_rounds += 1
                    if stagnant_rounds >= 2:
                        break
                else:
                    stagnant_rounds = 0
                page.mouse.wheel(0, 3000)
                time.sleep(1.2 + random.random())

            tweets = list(collected.values())[:limit]
            log.info("@%s: got %d tweets", handle, len(tweets))
            # KOL 间随机延迟,降低风控
            time.sleep(random.uniform(5.0, 10.0))
            return tweets
        finally:
            page.close()

    def _parse_article(self, art, expected_handle: str) -> RawTweet | None:
        try:
            # 跳过转推 / 置顶
            social_ctx = art.query_selector('[data-testid="socialContext"]')
            if social_ctx:
                ctx_text = (social_ctx.inner_text() or "").lower()
                if "pinned" in ctx_text or "reposted" in ctx_text or "置顶" in ctx_text or "转推" in ctx_text:
                    return None

            # tweet id + url
            tweet_link = art.query_selector('a[href*="/status/"]')
            if not tweet_link:
                return None
            href = tweet_link.get_attribute("href") or ""
            m = _TWEET_ID_RE.search(href)
            if not m:
                return None
            tweet_id = m.group(1)
            url = f"https://x.com{href}" if href.startswith("/") else href

            # 作者 handle(从 url 取,确认是当前 KOL)
            author = href.split("/")[1] if href.startswith("/") else expected_handle
            if author.lower() != expected_handle.lower():
                return None  # 跳过被引用/被回复的其他人推文

            # 文本
            txt_el = art.query_selector('[data-testid="tweetText"]')
            text = txt_el.inner_text() if txt_el else ""

            # 时间
            time_el = art.query_selector("time")
            posted_at = dt.datetime.now(dt.UTC)
            if time_el:
                dt_attr = time_el.get_attribute("datetime")
                if dt_attr:
                    try:
                        posted_at = dt.datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
                    except ValueError:
                        pass

            # 互动数
            def _count(testid: str) -> int:
                el = art.query_selector(f'[data-testid="{testid}"]')
                if not el:
                    return 0
                # aria-label 是 "12 Likes" / "1,234 Reposts" / "0 replies"
                aria = el.get_attribute("aria-label") or ""
                m = re.match(r"([\d,.]+[KMB]?)", aria.strip())
                return _parse_count(m.group(1)) if m else 0

            return RawTweet(
                kol_handle=expected_handle,
                tweet_id=tweet_id,
                url=url,
                text=text,
                lang="en",
                posted_at=posted_at,
                likes=_count("like"),
                retweets=_count("retweet"),
                replies=_count("reply"),
            )
        except Exception as e:
            log.debug("parse article failed: %s", e)
            return None


def _engagement_score(likes: int, retweets: int, replies: int) -> float:
    """归一化 Twitter 互动分到 0-100。
    1k 互动 ~50 分,10k ~75 分,100k+ ~ 100 分。
    """
    import math
    raw = likes + retweets * 2 + replies
    if raw <= 0:
        return 0.0
    return min(100.0, 12.5 * math.log10(raw + 10))


class PlaywrightSignalSource:
    """SignalSource 适配:wrap PlaywrightTweetSource,产出 Signal。

    依赖 KOL seed + ranker,内部聚合多个 KOL 的推文。
    """

    def __init__(self, top_kol_ratio: float | None = None,
                 daily_limit_per_category: int | None = None,
                 delay_min_s: float = 5.0, delay_max_s: float = 10.0):
        from fiinfo.config import get_settings
        s = get_settings()
        self.top_kol_ratio = top_kol_ratio if top_kol_ratio is not None else s.top_kol_ratio
        self.limit_per_kol = daily_limit_per_category or s.daily_limit_per_category
        self._inner = PlaywrightTweetSource(
            auth_token=s.twitter_auth_token, ct0=s.twitter_ct0,
        )
        # 把延迟参数透传(便于配置文件控制)
        # 注:PlaywrightTweetSource 当前用硬编码 5-10s,这里参数留以备未来扩展

    def close(self):
        self._inner.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def fetch(self) -> list[Signal]:
        from fiinfo.kol.ranker import top_n_by_category
        from fiinfo.kol.seed_loader import load_seed_kols

        seed = load_seed_kols()
        top = top_n_by_category(seed, ratio=self.top_kol_ratio)
        out: list[Signal] = []
        for k in top:
            raws = self._inner.fetch_recent(k.handle, limit=self.limit_per_kol)
            for rt in raws:
                out.append(Signal(
                    source_kind="twitter",
                    source_name=k.handle,
                    external_id=rt.tweet_id,
                    url=rt.url,
                    title=rt.text[:80].replace("\n", " "),
                    text=rt.text,
                    posted_at=rt.posted_at,
                    score=_engagement_score(rt.likes, rt.retweets, rt.replies),
                    raw_score={"likes": rt.likes, "retweets": rt.retweets, "replies": rt.replies},
                    category=k.category,
                    lang=rt.lang,
                    author_handle=k.handle,
                ))
        return out
