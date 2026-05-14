import math
from collections import defaultdict

from fiinfo.models import Kol


def top_n_by_category(kols: list[Kol], ratio: float = 0.25, min_per_cat: int = 1) -> list[Kol]:
    buckets: dict[str, list[Kol]] = defaultdict(list)
    for k in kols:
        buckets[k.category].append(k)
    out: list[Kol] = []
    for items in buckets.values():
        items.sort(key=lambda k: k.followers, reverse=True)
        n = max(min_per_cat, math.ceil(len(items) * ratio))
        out.extend(items[:n])
    return out
