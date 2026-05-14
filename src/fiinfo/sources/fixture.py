import datetime as dt
import json
from pathlib import Path

from fiinfo.sources.base import RawTweet, TweetSource
from fiinfo.sources.base_signal import Signal

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


class FixtureSignalSource:
    """Mock SignalSource:从 fixtures/tweets_sample.json 读全部 → Signal 列表。"""

    def __init__(self, path: Path | None = None):
        self._inner = FixtureTweetSource(path=path)

    def fetch(self) -> list[Signal]:
        from fiinfo.kol.seed_loader import load_seed_kols
        seed_cat = {k.handle: k.category for k in load_seed_kols()}
        out: list[Signal] = []
        for rt in self._inner._all:  # noqa: SLF001
            out.append(Signal(
                source_kind="twitter",
                source_name=rt.kol_handle,
                external_id=rt.tweet_id,
                url=rt.url,
                title=rt.text[:80],
                text=rt.text,
                posted_at=rt.posted_at,
                score=float(rt.likes + rt.retweets * 2 + rt.replies),
                raw_score={"likes": rt.likes, "retweets": rt.retweets, "replies": rt.replies},
                category=seed_cat.get(rt.kol_handle, ""),
                lang=rt.lang,
                author_handle=rt.kol_handle,
            ))
        return out
