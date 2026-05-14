"""DefiLlama signal sources:TVL / Raises / Hacks。

DefiLlama 公开 API,无 key,无限速。
"""
from __future__ import annotations

import datetime as dt
import logging

import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_BASE = "https://api.llama.fi"
_TIMEOUT = 30.0

# DefiLlama category → 我们的 9 类目
_CAT_MAP = {
    # DEXAMM
    "Dexs": "DEXAMM", "Dexes": "DEXAMM", "DEX": "DEXAMM",
    "Dex Aggregator": "DEXAMM", "DEX Aggregator": "DEXAMM",
    "Yield": "DEXAMM", "Yield Aggregator": "DEXAMM",
    "Lending": "DEXAMM", "CDP": "DEXAMM",
    "Synthetics": "DEXAMM",
    # PerpDEX
    "Derivatives": "PerpDEX", "Perps Aggregator": "PerpDEX",
    "Options": "PerpDEX", "Options Vault": "PerpDEX",
    # Restaking
    "Liquid Staking": "Restaking", "Liquid Restaking": "Restaking",
    "Restaking": "Restaking",
    # RWA
    "RWA": "RWA", "RWA Lending": "RWA", "Treasury Manager": "RWA",
    # Stablecoin
    "Stablecoin Issuer": "Stablecoin", "Algo-Stables": "Stablecoin",
    "Reserve Currency": "Stablecoin",
    # Prediction
    "Prediction Market": "Prediction",
    # AIAgent
    "AI Agent": "AIAgent", "Decentralized Compute": "AIAgent",
    "AI": "AIAgent",
    # InfraL2
    "Rollup": "InfraL2", "Bridge": "InfraL2", "Cross Chain": "InfraL2",
    "Chain": "InfraL2", "Rollup-as-a-Service": "InfraL2",
    "Indexer": "InfraL2", "Oracle": "InfraL2",
    # Wallet
    "Wallet": "Wallet", "Wallets": "Wallet",
}


def _map_category(llama_cat: str | None) -> str:
    """命中映射返回我们类目,否则空串让上游 reclassify 文本处理。"""
    if not llama_cat:
        return ""
    return _CAT_MAP.get(llama_cat, "")


def _http_get_json(path: str, silent_codes: tuple[int, ...] = ()) -> dict | list | None:
    try:
        r = httpx.get(f"{_BASE}{path}", timeout=_TIMEOUT,
                      headers={"User-Agent": "fiinfo/0.1"})
        if r.status_code in silent_codes:
            log.info("DefiLlama %s returned %d (silently skipped)", path, r.status_code)
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("DefiLlama %s failed: %s", path, e)
        todo_add(f"DefiLlama {path} 请求失败: {type(e).__name__}: {e}")
        return None


def _norm_score(value: float, anchor: float = 100.0) -> float:
    """对绝对值做 log-like 归一化到 0-100。"""
    import math
    a = abs(value)
    if a <= 0:
        return 0.0
    return min(100.0, 50.0 + 12.5 * math.log10(max(a, 1.0) / max(anchor, 1.0) + 1))


# ─────────────────── TVL ───────────────────

class TVLSource:
    """24h TVL 涨跌幅 top N 协议。score 用绝对变化幅度归一化。"""

    def __init__(self, top_n: int = 30, min_change_pct: float = 3.0):
        self.top_n = top_n
        self.min_change_pct = min_change_pct

    def fetch(self) -> list[Signal]:
        data = _http_get_json("/protocols")
        if not isinstance(data, list):
            return []
        # 过滤:有 TVL & 24h change 绝对值 ≥ 阈值
        rows = [
            p for p in data
            if (p.get("tvl") or 0) > 1_000_000
            and abs(p.get("change_1d") or 0) >= self.min_change_pct
        ]
        rows.sort(key=lambda p: abs(p.get("change_1d") or 0), reverse=True)
        rows = rows[: self.top_n]

        now = dt.datetime.now(dt.UTC)
        out: list[Signal] = []
        for p in rows:
            slug = p.get("slug") or p.get("name", "").lower().replace(" ", "-")
            change_1d = float(p.get("change_1d") or 0)
            tvl = float(p.get("tvl") or 0)
            name = p.get("name", slug)
            direction = "📈" if change_1d > 0 else "📉"
            text = (f"{direction} {name} TVL {change_1d:+.2f}% (24h) → ${tvl:,.0f} 总锁仓。"
                    f"类目: {p.get('category', '?')}, 链: {','.join(p.get('chains', [])[:3])}")
            out.append(Signal(
                source_kind="defillama_tvl",
                source_name=slug,
                external_id=f"tvl-{slug}-{now.strftime('%Y%m%d')}",
                url=f"https://defillama.com/protocol/{slug}",
                title=f"{name} TVL {change_1d:+.2f}% in 24h",
                text=text,
                posted_at=now,
                score=_norm_score(change_1d, anchor=5.0),
                raw_score={"change_1d": change_1d, "tvl_usd": tvl},
                category=_map_category(p.get("category")),
                lang="en",
                author_handle=slug,
            ))
        return out


# ─────────────────── Raises ───────────────────

class RaisesSource:
    """最近融资公告。score 用融资额对数归一化。"""

    def __init__(self, since_days: int = 7):
        self.since_days = since_days

    def fetch(self) -> list[Signal]:
        # /raises 现在要付费 API key,402 时安静跳过
        data = _http_get_json("/raises", silent_codes=(402, 403))
        if not isinstance(data, dict):
            return []
        raises = data.get("raises") or []
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=self.since_days)
        out: list[Signal] = []
        for r in raises:
            ts = r.get("date") or 0
            if not ts:
                continue
            posted = dt.datetime.fromtimestamp(int(ts), tz=dt.UTC)
            if posted < cutoff:
                continue
            name = r.get("name") or "Unknown"
            amount = float(r.get("amount") or 0)  # 单位 USD,有时是 millions(根据字段)
            # DefiLlama 这字段单位经常变,做个 sanity:< 1000 视为单位 M
            amount_usd = amount * 1_000_000 if 0 < amount < 1000 else amount
            stage = r.get("round") or r.get("stage") or ""
            sector = r.get("sector") or r.get("category") or ""
            chains = r.get("chains") or []
            lead = (r.get("leadInvestors") or [""])[0]
            text = (f"💰 {name} 完成 {stage} 融资,金额约 ${amount_usd:,.0f}"
                    f"{'（领投:' + lead + '）' if lead else ''}。"
                    f"赛道: {sector},链: {','.join(chains[:3])}")
            out.append(Signal(
                source_kind="defillama_raises",
                source_name=name,
                external_id=f"raise-{name.lower().replace(' ', '-')}-{int(ts)}",
                url=r.get("source") or "https://defillama.com/raises",
                title=f"{name} raised {stage}",
                text=text,
                posted_at=posted,
                score=min(100.0, 25.0 + 10.0 * (amount_usd / 10_000_000)),
                raw_score={"amount_usd": amount_usd, "stage": stage},
                category=_map_category(sector),
                lang="en",
                author_handle="defillama",
            ))
        return out


# ─────────────────── Hacks ───────────────────

class HacksSource:
    """近期安全事件 / 黑客攻击。score 用损失金额归一化。"""

    def __init__(self, since_days: int = 14):
        self.since_days = since_days

    def fetch(self) -> list[Signal]:
        data = _http_get_json("/hacks")
        if not isinstance(data, list):
            return []
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=self.since_days)
        out: list[Signal] = []
        for h in data:
            ts = h.get("date") or 0
            if not ts:
                continue
            posted = dt.datetime.fromtimestamp(int(ts), tz=dt.UTC)
            if posted < cutoff:
                continue
            name = h.get("name") or "Unknown"
            amount = float(h.get("amount") or 0)  # USD
            technique = h.get("technique") or ""
            classification = h.get("classification") or ""
            chains = h.get("chain") or []
            if isinstance(chains, str):
                chains = [chains]
            text = (f"🚨 {name} 被攻击,损失约 ${amount:,.0f}。"
                    f"手法: {technique},分类: {classification},链: {','.join(chains[:3])}")
            out.append(Signal(
                source_kind="defillama_hacks",
                source_name=name,
                external_id=f"hack-{name.lower().replace(' ', '-')}-{int(ts)}",
                url=h.get("source") or "https://defillama.com/hacks",
                title=f"{name} hacked: ${amount:,.0f}",
                text=text,
                posted_at=posted,
                score=min(100.0, 30.0 + 15.0 * (amount / 1_000_000)),
                raw_score={"amount_usd": amount, "technique": technique},
                category="",  # 让 reclassify 关键词处理(可能落入 Restaking/DEXAMM/RWA 等)
                lang="en",
                author_handle="defillama",
            ))
        return out
