"""跨源融合:把当日全部 signals 喂给 LLM,识别 Top-N stories。

输出 dict 列表,每条:
{
  "rank": 1,
  "title": "Hyperliquid HIP-3 上线",
  "narrative": "3-5 句背景",
  "sources": [{"kind": "twitter", "name": "HyperliquidX", "url": "..."}, ...],
  "category": "PerpDEX"
}
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from fiinfo.config import get_settings

log = logging.getLogger(__name__)

_PROMPT = """你是 Web3 资讯总编。下面是过去 24 小时来自 Twitter、DefiLlama、CoinGecko、Snapshot、GitHub、新闻 RSS 等多个源的高热信号 (共 {n} 条),按重要性识别出当日 Top {k} 重大事件:

要求:
1. 每件事独立、不重复;同一事件多源报道时合并为一条 story
2. 每条 story 输出严格 JSON 对象,包含:
   - "rank": 排名 1-{k}
   - "title": 一句话标题(中文,≤25 字)
   - "narrative": 3-5 句中文背景,包含具体数据(金额/百分比/参与方)
   - "category": 必须是这九个之一: PerpDEX / DEXAMM / Wallet / Stablecoin / RWA / Prediction / AIAgent / Restaking / InfraL2
   - "sources": 数组,每个出处是 {{"kind": "twitter/defillama_tvl/...", "name": "出处名", "url": "完整 url"}}
3. 整体输出一个 JSON 数组,不要其他文字、不要 markdown 代码块

输入信号(格式:[score]<source_kind> @author | url | text):
{items}

直接输出 JSON 数组:
"""


def _format_signals(signals: list, max_items: int = 200) -> str:
    """格式化 signals 给 LLM。按 score 倒序取 top max_items。"""
    sorted_ = sorted(signals, key=lambda s: getattr(s, "score", 0), reverse=True)[:max_items]
    lines = []
    for s in sorted_:
        author = getattr(s, "author_handle", "") or getattr(s, "source_name", "")
        text = (s.text or "").replace("\n", " ")[:200]
        lines.append(f"[{s.score:.0f}]<{s.source_kind}> @{author} | {s.url} | {text}")
    return "\n".join(lines)


def _extract_json(raw: str) -> list[dict[str, Any]]:
    """从 LLM 返回里抓 JSON 数组(容忍代码块)。"""
    if not raw:
        return []
    # 去除可能的 markdown 代码块
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # 找第一个 [ 到最后一个 ]
    start = raw.find("[")
    end = raw.rfind("]")
    if start < 0 or end < 0:
        return []
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        log.warning("top_stories: JSON parse failed (%s); raw head: %s", e, raw[:200])
        return []
    if not isinstance(data, list):
        return []
    return data


def generate_top_stories(signals: list, k: int = 10, summarizer=None) -> list[dict[str, Any]]:
    """跨源融合产出 Top-K stories。

    `summarizer`:复用 summarize_orch._make_summarizer 的实例,需有 .client 与 .model 属性
    """
    if not signals:
        return []
    if summarizer is None:
        from fiinfo.summarize_orch import _make_summarizer
        summarizer = _make_summarizer()
    client = getattr(summarizer, "client", None)
    model = getattr(summarizer, "model", None)
    if client is None or model is None:
        log.warning("top_stories: summarizer lacks client/model, skipping")
        return []

    items = _format_signals(signals)
    prompt = _PROMPT.format(n=min(len(signals), 200), k=k, items=items)
    settings = get_settings()
    log.info("top_stories: calling %s for %d signals → top %d", model, len(signals), k)

    # 兼容 Anthropic (messages.create) 与 OpenAI 兼容 (chat.completions.create)
    raw = ""
    try:
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            resp = client.chat.completions.create(
                model=model, max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.choices[0].message.content or ""
        else:
            resp = client.messages.create(
                model=model, max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
    except Exception as e:
        log.warning("top_stories LLM call failed: %s", e)
        return []
    _ = settings  # avoid unused

    stories = _extract_json(raw)
    # 兜底:校验字段
    cleaned: list[dict[str, Any]] = []
    for i, st in enumerate(stories[:k], 1):
        if not isinstance(st, dict):
            continue
        cleaned.append({
            "rank": int(st.get("rank") or i),
            "title": str(st.get("title", "")).strip(),
            "narrative": str(st.get("narrative", "")).strip(),
            "category": str(st.get("category", "")).strip(),
            "sources": st.get("sources") or [],
        })
    return cleaned
