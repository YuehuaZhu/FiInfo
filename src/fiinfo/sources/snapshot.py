"""Snapshot 治理提案(GraphQL)。"""
from __future__ import annotations

import datetime as dt
import logging

import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_URL = "https://hub.snapshot.org/graphql"

# DAO space → 我们 9 类目
_SPACE_CAT = {
    "uniswapgovernance.eth": "DEXAMM", "uniswap": "DEXAMM",
    "aavedao.eth": "DEXAMM", "aave.eth": "DEXAMM",
    "lido-snapshot.eth": "Restaking", "lido": "Restaking",
    "opcollective.eth": "InfraL2", "optimism": "InfraL2",
    "ens.eth": "InfraL2",
    "arbitrumfoundation.eth": "InfraL2", "arbitrum": "InfraL2",
    "balancer.eth": "DEXAMM",
    "gitcoindao.eth": "InfraL2",
    "makerdao.eth": "Stablecoin", "sky.eth": "Stablecoin",
}


_QUERY = """
query ($spaces: [String]!, $first: Int!) {
  proposals(
    where: { space_in: $spaces, state: "active" }
    first: $first
    orderBy: "created"
    orderDirection: desc
  ) {
    id
    title
    body
    start
    end
    state
    scores_total
    votes
    link
    space { id name }
  }
}
"""


class ProposalsSource:
    def __init__(self, spaces: list[str] | None = None, first: int = 30):
        self.spaces = spaces or list(_SPACE_CAT.keys())
        self.first = first

    def fetch(self) -> list[Signal]:
        try:
            r = httpx.post(_URL, timeout=30.0,
                           json={"query": _QUERY, "variables": {"spaces": self.spaces, "first": self.first}},
                           headers={"User-Agent": "fiinfo/0.1"})
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning("Snapshot GraphQL failed: %s", e)
            todo_add(f"Snapshot 查询失败: {type(e).__name__}")
            return []

        proposals = (data.get("data") or {}).get("proposals") or []
        out: list[Signal] = []
        for p in proposals:
            sp = (p.get("space") or {}).get("id", "")
            sp_name = (p.get("space") or {}).get("name", sp)
            cat = _SPACE_CAT.get(sp, "")
            posted = dt.datetime.fromtimestamp(int(p.get("start") or 0), tz=dt.UTC)
            votes = int(p.get("votes") or 0)
            title = p.get("title", "")
            body = (p.get("body") or "")[:400]
            link = p.get("link") or f"https://snapshot.org/#/{sp}/proposal/{p.get('id')}"
            out.append(Signal(
                source_kind="snapshot",
                source_name=sp_name,
                external_id=f"snap-{p.get('id')}",
                url=link,
                title=f"🗳️ {sp_name}: {title}",
                text=f"🗳️ {sp_name} 治理提案投票中:{title}\n{body}",
                posted_at=posted,
                score=min(100.0, 30.0 + votes / 50),
                raw_score={"votes": votes, "scores_total": p.get("scores_total")},
                category=cat,
                lang="en",
                author_handle=sp_name,
            ))
        return out
