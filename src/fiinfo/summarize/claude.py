import logging

from fiinfo.config import get_settings
from fiinfo.models import Tweet
from fiinfo.summarize.base import Summarizer

log = logging.getLogger(__name__)

_PROMPT = """你是 Web3 资讯编辑。下面是 {category} 类目今日 KOL 高热推文列表,请输出 Markdown 摘要:
- 用 3-5 条要点概括今日动向
- 每条要点结尾用 [[tweet_id]](url) 标注主要出处
- 保持中文输出,但保留英文专有名词
- 不要编造未在原文出现的事实

推文列表:
{items}
"""


def _format_items(tweets: list[Tweet]) -> str:
    return "\n".join(f"- [{t.tweet_id}] ({t.url}) {t.text}" for t in tweets)


class ClaudeSummarizer(Summarizer):
    def __init__(self, client=None, model: str | None = None):
        settings = get_settings()
        if client is None:
            from anthropic import Anthropic
            client = Anthropic(api_key=settings.anthropic_api_key)
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
