"""CoinGecko trending coins/NFTs。"""
from __future__ import annotations

import datetime as dt
import logging

import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_URL = "https://api.coingecko.com/api/v3/search/trending"


class TrendingSource:
    """24h 搜索量飙升的 top 币种 + NFT 系列。"""

    def fetch(self) -> list[Signal]:
        try:
            r = httpx.get(_URL, timeout=20.0, headers={"User-Agent": "fiinfo/0.1"})
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning("CoinGecko trending failed: %s", e)
            todo_add(f"CoinGecko trending 请求失败: {type(e).__name__}: {e}")
            return []

        now = dt.datetime.now(dt.UTC)
        out: list[Signal] = []
        for entry in (data.get("coins") or []):
            item = entry.get("item") or {}
            symbol = item.get("symbol", "?").upper()
            name = item.get("name", symbol)
            rank = item.get("market_cap_rank") or 9999
            price_btc = item.get("price_btc") or 0
            slug = item.get("id") or name.lower().replace(" ", "-")
            score = max(0.0, 100.0 - rank * 0.1) if rank < 1000 else 50.0
            out.append(Signal(
                source_kind="coingecko_trending",
                source_name=slug,
                external_id=f"cg-trend-{slug}-{now.strftime('%Y%m%d')}",
                url=f"https://www.coingecko.com/en/coins/{slug}",
                title=f"🔥 {name} ({symbol}) trending",
                text=(f"🔥 ${symbol} {name} 进入 CoinGecko 24h 搜索飙升榜。"
                      f"市值排名: #{rank}, BTC 价: {price_btc:.8f}"),
                posted_at=now,
                score=score,
                raw_score={"market_cap_rank": rank, "price_btc": price_btc},
                category="",  # 让 reclassify 关键词处理
                lang="en",
                author_handle="coingecko",
            ))
        # NFT 部分按需也加进去,但分类弱,默认归 DEXAMM
        for entry in (data.get("nfts") or [])[:5]:
            name = entry.get("name", "Unknown NFT")
            slug = entry.get("id") or name.lower().replace(" ", "-")
            out.append(Signal(
                source_kind="coingecko_trending",
                source_name=slug,
                external_id=f"cg-nft-{slug}-{now.strftime('%Y%m%d')}",
                url=f"https://www.coingecko.com/en/nft/{slug}",
                title=f"🖼️ {name} NFT trending",
                text=f"🖼️ NFT 系列 {name} 进入 CoinGecko 趋势榜。",
                posted_at=now,
                score=40.0,
                raw_score={},
                category="",
                lang="en",
                author_handle="coingecko",
            ))
        return out
