import datetime as dt
import json
import uuid
from pathlib import Path

from fiinfo.publish.base import Publisher


class DryRunPublisher(Publisher):
    def __init__(self, outbox: Path = Path("outbox")):
        self.outbox = Path(outbox)
        self.outbox.mkdir(parents=True, exist_ok=True)

    def publish_threads(self, threads: list[list[str]]) -> list[str]:
        ids: list[str] = []
        for thread in threads:
            tid = f"dry-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
            (self.outbox / f"{tid}.json").write_text(
                json.dumps(thread, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            ids.append(tid)
        return ids
