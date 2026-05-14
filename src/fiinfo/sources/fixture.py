import datetime as dt
import json
from pathlib import Path

from fiinfo.sources.base import RawTweet, TweetSource

DEFAULT = Path(__file__).resolve().parents[3] / "fixtures" / "tweets_sample.json"


class FixtureTweetSource(TweetSource):
    def __init__(self, path: Path | None = None):
        p = path or DEFAULT
        self._all = [self._parse(r) for r in json.loads(p.read_text(encoding="utf-8"))]

    @staticmethod
    def _parse(r: dict) -> RawTweet:
        return RawTweet(
            kol_handle=r["kol_handle"],
            tweet_id=r["tweet_id"],
            url=r["url"],
            text=r["text"],
            lang=r.get("lang", "en"),
            posted_at=dt.datetime.fromisoformat(r["posted_at"].replace("Z", "+00:00")),
            likes=r["likes"],
            retweets=r["retweets"],
            replies=r["replies"],
        )

    def fetch_recent(self, handle: str, limit: int = 30) -> list[RawTweet]:
        return [t for t in self._all if t.kol_handle == handle][:limit]
