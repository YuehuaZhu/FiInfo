import datetime as dt
import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fiinfo.config import get_settings
from fiinfo.db import session_scope
from fiinfo.models import Kol, SignalRow, Summary, TopStory, Tweet

_TPL_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TPL_DIR), autoescape=select_autoescape(["html"]))


_LINK_DOUBLE = re.compile(r"\[\[([^\]]+)\]\]\(([^)]+)\)")   # 旧:[[id]](url)
_LINK_SINGLE = re.compile(r"\[(@[^\]]+)\]\(([^)]+)\)")       # 新:[@handle](url)
# 抓所有引用:group(1)=完整,group(2)=显示文本(@handle 或 [id]),group(3)=url
_ALL_LINKS = re.compile(r"(\[(@[^\]]+|\[[^\]]+\])\]\(([^)]+)\))")


def _dedup_citations_in_line(ln: str) -> str:
    """同一行里同一作者(@handle)或同一 url 的引用只保留第一次出现。

    用户希望"@saylor @saylor"这种连续重名也不出现 —— 即使 url 不同,
    同一个 handle 在一条要点里也只显示一次。
    """
    seen_keys: set[str] = set()

    def _keep(m: re.Match) -> str:
        full, label, url = m.group(1), m.group(2), m.group(3)
        # 用 handle(label)作 key,如果是旧 [[id]] 格式则用 url 作 key
        key = label if label.startswith("@") else url
        if key in seen_keys:
            return ""
        seen_keys.add(key)
        return full

    cleaned = _ALL_LINKS.sub(_keep, ln)
    # 折叠引用之间的多余空格 / 标点前空格
    cleaned = re.sub(r"\s+([。,，。;;])", r"\1", cleaned)
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
        date=today, total_tweets=total, summaries=by_cat, top_stories=[],
        source_pages=[],
    )
    out = out_dir / f"briefing-{today}.html"
    out.write_text(html, encoding="utf-8")
    return out


def render_today_from_signals(out_dir: Path | None = None, today: str | None = None) -> Path:
    """新版渲染:读 signals 表(支持多源混排)。

    与 render_today 并存(legacy 通过 tweets)。模板复用同一个 briefing.html.j2,
    每条 signal 用 author_handle 替代原 KOL 查找。
    """
    settings = get_settings()
    today = today or dt.date.today().isoformat()
    out_dir = out_dir or settings.data_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with session_scope() as s:
        summaries = s.query(Summary).filter(Summary.date == today).all()
        sigs_all = s.query(SignalRow).all()
        sigs_by_key = {f"{x.source_kind}:{x.external_id}": x for x in sigs_all}

        by_cat: dict[str, dict] = {}
        for sm in summaries:
            keys = [k for k in (sm.source_signal_ids.split(",") if sm.source_signal_ids else []) if k]
            picked = [sigs_by_key[k] for k in keys if k in sigs_by_key]
            picked.sort(key=lambda x: x.score, reverse=True)
            view = [_signal_view(x) for x in picked]
            by_cat[sm.category] = {"summary_html": _md_to_html_basic(sm.content_md), "tweets": view}

        total = len(sigs_all)

        # Top stories
        top_rows = s.query(TopStory).filter(TopStory.date == today).order_by(TopStory.rank).all()
        top_stories = []
        for ts in top_rows:
            try:
                sources = json.loads(ts.sources_json or "[]")
            except Exception:
                sources = []
            top_stories.append({
                "rank": ts.rank,
                "title": ts.title,
                "narrative": ts.narrative,
                "category": ts.category,
                "sources": sources,
            })

        # ─── 按渠道分组 ───
        by_source = _group_by_source(sigs_all)

        # 生成每渠道独立页 + 收集导航数据
        sub_dir = out_dir / "by-source"
        sub_dir.mkdir(parents=True, exist_ok=True)
        source_pages: list[dict] = []
        for kind, sigs in by_source.items():
            page_path = _render_source_page(kind, sigs, sub_dir, today)
            source_pages.append({
                "kind": kind,
                "count": len(sigs),
                "page": f"by-source/{page_path.name}",  # 相对主页
                "top_preview": [_signal_view(x) for x in sigs[:3]],
            })
        source_pages.sort(key=lambda x: x["count"], reverse=True)

    html = _env.get_template("briefing.html.j2").render(
        date=today, total_tweets=total, summaries=by_cat, top_stories=top_stories,
        source_pages=source_pages,
    )
    out = out_dir / f"briefing-{today}.html"
    out.write_text(html, encoding="utf-8")
    return out


def _signal_view(x) -> dict:
    """SignalRow → 模板用 dict。"""
    try:
        raw = json.loads(x.raw_score_json or "{}")
    except Exception:
        raw = {}
    return {
        "kol_handle": x.author_handle or x.source_name,
        "text": x.text,
        "url": x.url,
        "likes": int(raw.get("likes", 0)),
        "retweets": int(raw.get("retweets", 0)),
        "source_kind": x.source_kind,
        "title": x.title,
        "score": x.score,
        "posted_at": x.posted_at.isoformat() if x.posted_at else "",
    }


def _group_by_source(signals) -> dict[str, list]:
    """按 source_kind 分组,每组内按 score 倒序。"""
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for s in signals:
        buckets[s.source_kind].append(s)
    for k in buckets:
        buckets[k].sort(key=lambda x: x.score, reverse=True)
    return dict(buckets)


def _render_source_page(kind: str, signals: list, sub_dir: Path, today: str) -> Path:
    """生成单个渠道的独立 HTML 页(`by-source/<kind>-YYYY-MM-DD.html`)。"""
    view = [_signal_view(x) for x in signals]
    html = _env.get_template("source_page.html.j2").render(
        date=today, kind=kind, total=len(signals), signals=view,
        back_to_index="../briefing-" + today + ".html",
    )
    out = sub_dir / f"{kind}-{today}.html"
    out.write_text(html, encoding="utf-8")
    return out
