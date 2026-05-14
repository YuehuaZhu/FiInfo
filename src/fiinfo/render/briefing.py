import datetime as dt
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.models import Kol, Summary, Tweet

_TPL_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TPL_DIR), autoescape=select_autoescape(["html"]))


_LINK_DOUBLE = re.compile(r"\[\[([^\]]+)\]\]\(([^)]+)\)")   # 旧:[[id]](url)
_LINK_SINGLE = re.compile(r"\[(@[^\]]+)\]\(([^)]+)\)")       # 新:[@handle](url)
_ALL_LINKS = re.compile(r"(\[(?:@[^\]]+|\[[^\]]+\])\]\(([^)]+)\))")  # 抓所有引用 + url


def _dedup_citations_in_line(ln: str) -> str:
    """同一行里相同 url 的引用只保留第一次出现。"""
    seen_urls: set[str] = set()

    def _keep(m: re.Match) -> str:
        full, url = m.group(1), m.group(2)
        if url in seen_urls:
            return ""
        seen_urls.add(url)
        return full

    # 折叠引用之间的多余空格
    cleaned = _ALL_LINKS.sub(_keep, ln)
    cleaned = re.sub(r"\s+([。,,。;;])", r"\1", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned).rstrip()
    return cleaned


def _md_to_html_basic(md: str) -> str:
    """最小 markdown:## 标题、- 列表、[[id]](url) 链接保留为可点击。"""
    html_lines: list[str] = []
    in_list = False
    for raw in md.splitlines():
        ln = raw.rstrip()
        if not ln.strip():
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        # 行内 url 去重(防止 LLM 把同一 url 重复引用)
        ln = _dedup_citations_in_line(ln)
        # 转链接 (两种格式)
        ln_html = _LINK_DOUBLE.sub(r'<a href="\2" target="_blank">[\1]</a>', ln)
        ln_html = _LINK_SINGLE.sub(r'<a href="\2" target="_blank">\1</a>', ln_html)
        if ln.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{ln_html[3:]}</h3>")
        elif ln.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{ln_html[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{ln_html}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def render_today(out_dir: Path | None = None, today: str | None = None) -> Path:
    settings = get_settings()
    today = today or dt.date.today().isoformat()
    out_dir = out_dir or settings.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with session_scope() as s:
        summaries = s.query(Summary).filter(Summary.date == today).all()
        tweets_all = s.query(Tweet).all()
        kols = {k.id: k for k in s.query(Kol).all()}
        tweets_by_id = {t.tweet_id: t for t in tweets_all}

        by_cat: dict[str, dict] = {}
        for sm in summaries:
            tids = [x for x in (sm.source_tweet_ids.split(",") if sm.source_tweet_ids else []) if x]
            ts = [tweets_by_id[tid] for tid in tids if tid in tweets_by_id]
            ts.sort(key=lambda t: t.likes + t.retweets * 2, reverse=True)
            view = [
                {
                    "kol_handle": kols[t.kol_id].handle if t.kol_id in kols else "?",
                    "text": t.text,
                    "url": t.url,
                    "likes": t.likes,
                    "retweets": t.retweets,
                }
                for t in ts
            ]
            by_cat[sm.category] = {"summary_html": _md_to_html_basic(sm.content_md), "tweets": view}

        total = len(tweets_all)

    html = _env.get_template("briefing.html.j2").render(
        date=today, total_tweets=total, summaries=by_cat
    )
    out = out_dir / f"briefing-{today}.html"
    out.write_text(html, encoding="utf-8")
    return out
