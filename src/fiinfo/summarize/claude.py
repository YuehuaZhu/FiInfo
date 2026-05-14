import logging

from fiinfo.config import get_settings
from fiinfo.models import Tweet
from fiinfo.summarize.base import Summarizer

log = logging.getLogger(__name__)

_PROMPT = """你是 Web3 资讯编辑。下面是 {category} 类目今日 KOL 高热推文列表,请输出 Markdown 摘要:
- 用 3-5 条要点概括今日动向
- 每条要点结尾用 [@handle](url) 标注主要出处(可同时多个,例如 [@cz_binance](url1) [@VitalikButerin](url2))
- handle 必须从下方"@handle"列里原样照抄,不要发明
- 保持中文输出,但保留英文专有名词
- 不要编造未在原文出现的事实

推文列表(格式:@handle | url | 正文):
{items}
"""


def _handle_of(t: Tweet) -> str:
    """安全获取 KOL handle。Tweet 与 Kol 在同一 session 内关联时可用。"""
    try:
        return t.kol.handle if t.kol else "unknown"
    except Exception:
        return "unknown"


def _format_items(tweets: list[Tweet]) -> str:
    return "\n".join(
        f"- @{_handle_of(t)} | {t.url} | {t.text}" for t in tweets
    )


class ClaudeSummarizer(Summarizer):
    def __init__(self, client=None, model: str | None = None):
        settings = get_settings()
        if client is None:
            from anthropic import Anthropic
            kwargs: dict = {}
            # 代理网关:auth_token + base_url(如 sub2api.sineai.cn)
            if settings.anthropic_auth_token:
                kwargs["auth_token"] = settings.anthropic_auth_token
            elif settings.anthropic_api_key:
                kwargs["api_key"] = settings.anthropic_api_key
            if settings.anthropic_base_url:
                kwargs["base_url"] = settings.anthropic_base_url
            client = Anthropic(**kwargs)
        self.client = client
        self.model = model or settings.anthropic_model

    def summarize_category(self, category: str, tweets: list[Tweet]) -> str:
        if not tweets:
            return f"## {category}\n(no tweets today)"
        prompt = _PROMPT.format(category=category, items=_format_items(tweets))
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
