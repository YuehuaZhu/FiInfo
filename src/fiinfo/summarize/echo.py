from fiinfo.models import Tweet
from fiinfo.summarize.base import Summarizer
from fiinfo.summarize.claude import _handle_of


class EchoSummarizer(Summarizer):
    """无 LLM key 时的 fallback:截取要点 + 保留出处链接。"""

    def summarize_category(self, category: str, tweets: list[Tweet]) -> str:
        if not tweets:
            return f"## {category}\n(no tweets today)"
        lines = [f"## {category} — Top {len(tweets)} (echo mock)"]
        for t in tweets[:10]:
            snippet = t.text[:160].replace("\n", " ")
            lines.append(f"- {snippet} [@{_handle_of(t)}]({t.url})")
        return "\n".join(lines)
