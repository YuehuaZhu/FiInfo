"""GitHub Trending(无官方 API,抓 HTML)。

只取 Solidity / Rust / TypeScript 三个语言的 daily trending repos,
过滤包含加密关键词的 description。
"""
from __future__ import annotations

import datetime as dt
import logging
import re

import httpx

from fiinfo.morning_todo import add as todo_add
from fiinfo.sources.base_signal import Signal

log = logging.getLogger(__name__)

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# 加密关键词:用于过滤非加密的 trending repo
_KW = re.compile(
    r"\b(blockchain|crypto|web3|defi|dao|nft|solidity|ethereum|solana|"
    r"bitcoin|zk|rollup|l2|smart\s*contract|onchain|on-chain|stablecoin|"
    r"hyperliquid|uniswap|wallet|cosmos|polkadot|cairo|move|fuel)\b",
    re.IGNORECASE,
)

# 抓 trending 卡片的简单正则(GitHub HTML 结构相对稳定)
_REPO_RE = re.compile(
    r'<article class="Box-row">[\s\S]*?'
    r'href="/(?P<repo>[^"]+/[^"]+)"[\s\S]*?'
    r'(?:<p[^>]*>(?P<desc>[\s\S]*?)</p>)?[\s\S]*?'
    r'</article>',
    re.IGNORECASE,
)


class TrendingSource:
    def __init__(self, languages: list[str] | None = None):
        self.languages = languages or ["solidity", "rust", "typescript"]

    def fetch(self) -> list[Signal]:
        out: list[Signal] = []
        for lang in self.languages:
            out.extend(self._fetch_lang(lang))
        return out

    def _fetch_lang(self, lang: str) -> list[Signal]:
        url = f"https://github.com/trending/{lang}?since=daily"
        try:
            r = httpx.get(url, timeout=20.0,
                          headers={"User-Agent": _UA, "Accept": "text/html"},
                          follow_redirects=True)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            log.warning("GitHub trending %s failed: %s", lang, e)
            todo_add(f"GitHub trending {lang} 失败: {type(e).__name__}")
            return []

        now = dt.datetime.now(dt.UTC)
        out: list[Signal] = []
        seen: set[str] = set()
        for m in _REPO_RE.finditer(html):
            repo = m.group("repo").strip()
            if repo in seen or "/" not in repo:
                continue
            seen.add(repo)
            desc = re.sub(r"<[^>]+>", "", m.group("desc") or "").strip()
            # 过滤非加密项目
            if lang.lower() != "solidity" and not _KW.search(desc + " " + repo):
                continue
            out.append(Signal(
                source_kind="github_trending",
                source_name=repo,
                external_id=f"gh-{lang}-{repo.replace('/', '-')}-{now.strftime('%Y%m%d')}",
                url=f"https://github.com/{repo}",
                title=f"🐙 {repo}",
                text=f"🐙 GitHub trending ({lang}): {repo}\n{desc or '(no description)'}",
                posted_at=now,
                score=55.0,
                raw_score={"language": lang},
                category="InfraL2",  # GitHub repo 默认归基础设施
                lang="en",
                author_handle=repo.split("/")[0],
            ))
        return out
