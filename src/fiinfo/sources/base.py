import datetime as dt
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawTweet:
    kol_handle: str
    tweet_id: str
    url: str
    text: str
    lang: str
    posted_at: dt.datetime
    likes: int
    retweets: int
    replies: int


class TweetSource(ABC):
    @abstractmethod
    def fetch_recent(self, handle: str, limit: int = 30) -> list[RawTweet]: ...
