from abc import ABC, abstractmethod

from fiinfo.models import Tweet


class Summarizer(ABC):
    @abstractmethod
    def summarize_category(self, category: str, tweets: list[Tweet]) -> str: ...
