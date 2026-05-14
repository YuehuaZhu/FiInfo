import logging

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base import RawTweet, TweetSource

log = logging.getLogger(__name__)


class PlaywrightTweetSource(TweetSource):
    """占位实现:有 auth_token 时尝试抓取;没有则记 TODO 并返回 []。

    一期不实现真实抓取(Twitter 反爬严格,需代理 + 随机延迟)。
    """

    def __init__(self, auth_token: str = ""):
        self.auth_token = auth_token
        if not auth_token:
            todo_add("配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取")

    def fetch_recent(self, handle: str, limit: int = 30) -> list[RawTweet]:
        if not self.auth_token:
            log.warning("PlaywrightTweetSource: no cookie, skipping %s", handle)
            return []
        log.warning("PlaywrightTweetSource: real fetch not yet implemented (placeholder) for %s", handle)
        return []
