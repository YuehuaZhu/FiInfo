from collections import defaultdict

from fiinfo.models import Tweet


def engagement_score(t: Tweet) -> int:
    return t.likes + t.retweets * 2 + t.replies


def top_per_category(tweets: list[Tweet], limit_per_cat: int = 30) -> dict[str, list[Tweet]]:
    buckets: dict[str, list[Tweet]] = defaultdict(list)
    for t in tweets:
        buckets[t.category or "uncategorized"].append(t)
    return {
        c: sorted(items, key=engagement_score, reverse=True)[:limit_per_cat]
        for c, items in buckets.items()
    }
