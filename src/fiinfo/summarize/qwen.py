"""千问(阿里 DashScope)摘要器。OpenAI 兼容。"""
from __future__ import annotations

import logging

from fiinfo.config import get_settings
from fiinfo.models import Tweet
from fiinfo.summarize.base import Summarizer
from fiinfo.summarize.claude import _PROMPT, _format_items

log = logging.getLogger(__name__)


class QwenSummarizer(Summarizer):
    def __init__(self, client=None, model: str | None = None):
        s = get_settings()
        if client is None:
            from openai import OpenAI
            client = OpenAI(api_key=s.dashscope_api_key, base_url=s.dashscope_base_url)
        self.client = client
        self.model = model or s.dashscope_model

    def summarize_category(self, category: str, tweets: list[Tweet]) -> str:
        if not tweets:
            return f"## {category}\n(no tweets today)"
        prompt = _PROMPT.format(category=category, items=_format_items(tweets))
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""
