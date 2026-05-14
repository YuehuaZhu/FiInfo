from __future__ import annotations

import re
from collections import defaultdict

from fiinfo.models import Tweet

# 推文文本关键词 → 类目映射。命中后覆写 tweet.category。
# 顺序决定优先级:列表上方的更优先(如 "stablecoin" 与 "L2" 同时出现优先归 Stablecoin)。
_KEYWORDS: list[tuple[str, list[str]]] = [
    ("PerpDEX", [
        r"\bhyperliquid\b", r"\bhip-?[34]\b", r"\bperp\s*dex\b", r"\bperpetuals?\b",
        r"\baster\b", r"\blighter\b", r"\bdydx\b", r"\bgmx\b", r"\bdrift\b",
        r"\bparadex\b", r"\bsynfutures\b",
    ]),
    ("Prediction", [
        r"\bpolymarket\b", r"\bkalshi\b", r"\bazuro\b", r"\bprediction\s*market",
        r"\blimitless\b", r"\btruemarkets\b", r"\bbinary\s*options?\b",
    ]),
    ("Restaking", [
        r"\beigenlayer\b", r"\beigenda\b", r"\brestak", r"\bsymbiotic\b", r"\bkarak\b",
        r"\bether\.?fi\b", r"\bpuffer\b", r"\brenzo\b", r"\bkelp\s*dao\b", r"\bswell\b",
        r"\blrt\b", r"\bavs\b",
    ]),
    ("RWA", [
        r"\brwa\b", r"\breal[- ]world\s*asset", r"\btokeniz", r"\bondo\b",
        r"\bplume\b", r"\bcentrifuge\b", r"\bmaple\b", r"\bgoldfinch\b",
        r"\btreasur\w*\s+token", r"\bblackrock\b", r"\bbuidl\b", r"\bsuperstate\b",
    ]),
    ("Stablecoin", [
        r"\busdc\b", r"\busdt\b", r"\busde\b", r"\busds\b", r"\busdy\b", r"\busd[bp]\b",
        r"\bstable\s*coin\b", r"\bstable\s*chain\b", r"\bcircle\s+arc\b", r"\barc\s+l1\b",
        r"\btether\b", r"\bcircle\b", r"\bethena\b", r"\bfrax\b", r"\bmakerdao\b",
        r"\bcrypto\s+card\b", r"\bagora\b",
    ]),
    ("AIAgent", [
        r"\bai\s*agent\b", r"\bagentic\b", r"\bai16z\b", r"\beliza(os)?\b",
        r"\bvirtuals\b", r"\bautonolas\b", r"\bolas\b", r"\bfetch\.?ai\b",
        r"\bbittensor\b", r"\bdepai\b", r"\baixbt\b", r"\bnous\b",
    ]),
    ("Wallet", [
        r"\bmetamask\b", r"\bphantom\b", r"\btrust\s*wallet\b", r"\brabby\b",
        r"\bzerion\b", r"\brainbow\b", r"\bsafe\b.*\bwallet\b", r"\bargent\b",
        r"\bkeplr\b", r"\bbackpack\b",
    ]),
    ("PerpDEX", [r"\bperp\b"]),  # 最后兜底关键词,避免误伤
    ("DEXAMM", [
        r"\buniswap\b", r"\b1inch\b", r"\bcurve\b\s*finance", r"\bpancake\s*swap\b",
        r"\bbalancer\b", r"\bsushi\b", r"\braydium\b", r"\bjupiter\b",
        r"\bhooks?\b.*\buniswap\b", r"\bv4\s+hooks?\b", r"\bamm\b",
    ]),
    ("InfraL2", [
        r"\bbase\b\s+(chain|network|l2)", r"\barbitrum\b", r"\boptimism\b",
        r"\bzksync\b", r"\bstarknet\b", r"\bscroll\b", r"\blinea\b",
        r"\bton\s+(blockchain|network|coin)\b", r"\btelegram\s*mini\s*app",
        r"\balchemy\b", r"\bmoralis\b", r"\bthirdweb\b", r"\bzk[- ]?rollup\b",
        r"\bzero[- ]?knowledge\b",
    ]),
]


def reclassify(text: str, default: str) -> str:
    """根据推文内容关键词覆写类目。

    没命中任何关键词时返回原 default(即 KOL 的归属类目)。
    """
    if not text:
        return default
    lower = text.lower()
    for cat, patterns in _KEYWORDS:
        for p in patterns:
            if re.search(p, lower):
                return cat
    return default


def engagement_score(t: Tweet) -> int:
    return t.likes + t.retweets * 2 + t.replies


def top_per_category(tweets: list[Tweet], limit_per_cat: int = 30) -> dict[str, list[Tweet]]:
    """按 tweet.category 分组取热度 top-N。

    上游 collect 阶段应该先调 reclassify 一次刷新 category。
    """
    buckets: dict[str, list[Tweet]] = defaultdict(list)
    for t in tweets:
        buckets[t.category or "uncategorized"].append(t)
    return {
        c: sorted(items, key=engagement_score, reverse=True)[:limit_per_cat]
        for c, items in buckets.items()
    }


def signal_score(s) -> float:
    """读 SignalRow.score(已归一化 0-100),用于 signals 表排序。"""
    return float(getattr(s, "score", 0.0) or 0.0)


def top_signals_per_category(signals, limit_per_cat: int = 30) -> dict[str, list]:
    """SignalRow 版本:按 category 分组,按 score 降序取 top。"""
    buckets: dict[str, list] = defaultdict(list)
    for s in signals:
        buckets[s.category or "uncategorized"].append(s)
    return {
        c: sorted(items, key=signal_score, reverse=True)[:limit_per_cat]
        for c, items in buckets.items()
    }
