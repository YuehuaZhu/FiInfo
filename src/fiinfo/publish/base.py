from abc import ABC, abstractmethod


class Publisher(ABC):
    @abstractmethod
    def publish_threads(self, threads: list[list[str]]) -> list[str]: ...
