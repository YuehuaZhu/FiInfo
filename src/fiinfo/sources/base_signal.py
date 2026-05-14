"""统一的 Signal 数据结构 + SignalSource 协议。

所有信息源(Twitter / DefiLlama / RSS / Reddit / ...)统一产出 Signal,
进流水线 → 分类 → 摘要 → 渲染。

设计原则:
- Signal 比 RawTweet 更通用,字段尽量不依赖单一源
- score 强制归一化到 0-100(各源各自计算 raw_score 后归一)
- raw_score 字典保留各源特有指标,渲染层可选择性展示
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Signal:
    source_kind: str           # "twitter" / "defillama" / "rss" / "reddit" / "snapshot" / "github" / ...
    source_name: str           # 源内的具体来源(KOL handle / protocol slug / subreddit / feed url)
    external_id: str           # 源内唯一标识(tweet_id / proposal_id / post_id / news_id)
    url: str
    title: str                 # 短标题(80 字内,推文用前 80 字截断)
    text: str                  # 长文本
    posted_at: dt.datetime
    score: float = 0.0         # 归一化 0-100
    raw_score: dict = field(default_factory=dict)
    category: str = ""         # 9 类目之一,可由 reclassify 覆写
    lang: str = "en"
    author_handle: str = ""    # 显示用,如 "@cz_binance" 的 cz_binance,DefiLlama 这种无主源留空


class SignalSource(Protocol):
    """所有信息源协议。

    实现类可以是普通 class,不必继承 —— Python Protocol 是结构化匹配。
    registry 会在构造后挂 `registry_name` 与 `kind` 属性。
    """
    def fetch(self) -> list[Signal]:
        """返回当前快照下的 signals。
        失败应吞掉异常并返回 [],由实现内部记 MORNING_TODO,不要让一个源挂掉整个流水线。
        """
        ...
