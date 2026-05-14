import datetime as dt
import json
import logging
from pathlib import Path

from fiinfo.collect import collect_all, collect_signals
from fiinfo.db import init_db, session_scope
from fiinfo.dispatch import dispatch_today
from fiinfo.models import SignalRow, TopStory
from fiinfo.render.briefing import render_today, render_today_from_signals
from fiinfo.sources.registry import DEFAULT_CONFIG, load_sources, top_stories_config
from fiinfo.summarize.top_stories import generate_top_stories
from fiinfo.summarize_orch import (
    summarize_channels_today,
    summarize_today,
    summarize_today_from_signals,
)

log = logging.getLogger(__name__)


def _maybe_generate_top_stories(force_mock: bool, today: str | None = None) -> int:
    """读 config.top_stories.enabled,若开启则跑跨源融合并写入 top_stories 表。"""
    cfg = top_stories_config()
    if not cfg["enabled"] or force_mock:
        return 0
    today = today or dt.date.today().isoformat()
    with session_scope() as s:
        signals = s.query(SignalRow).all()
        if not signals:
            return 0
        stories = generate_top_stories(signals, k=cfg["count"])
        if not stories:
            return 0
        # 清掉旧的当日 top stories
        s.query(TopStory).filter(TopStory.date == today).delete()
        for st in stories:
            s.add(TopStory(
                date=today,
                rank=st["rank"],
                title=st["title"],
                narrative=st["narrative"],
                category=st["category"],
                sources_json=json.dumps(st["sources"], ensure_ascii=False),
            ))
        return len(stories)


def _signals_mode_available(config_path: Path = DEFAULT_CONFIG) -> bool:
    if not config_path.exists():
        return False
    try:
        return len(load_sources(config_path)) > 0
    except Exception as e:
        log.warning("registry probe failed: %s", e)
        return False


def run_daily(
    source_name: str | None = None,
    dry_run: bool = True,
    force_mock_llm: bool = False,
    use_signals: bool | None = None,
) -> dict:
    """daily 流水线。

    `use_signals`:
      - None(默认):有 enabled sources 时走 signals 新路径,否则 legacy
      - True:强制走 signals
      - False:强制走 legacy
    """
    init_db()
    if use_signals is None:
        use_signals = _signals_mode_available() and source_name != "fixture"

    if use_signals:
        log.info("pipeline mode: signals (multi-source)")
        n_items = collect_signals()
        n_sum = summarize_today_from_signals(force_mock=force_mock_llm)
        n_chan = summarize_channels_today(force_mock=force_mock_llm)
        n_top = _maybe_generate_top_stories(force_mock_llm)
        briefing = render_today_from_signals()
        log.info("channel summaries: %d, top stories: %d", n_chan, n_top)
    else:
        log.info("pipeline mode: legacy (tweets only)")
        n_items = collect_all(source_name=source_name)
        n_sum = summarize_today(force_mock=force_mock_llm)
        briefing = render_today()

    n_disp = dispatch_today(dry_run=dry_run)
    result = {
        "items_collected": n_items,
        "tweets_collected": n_items,  # legacy 兼容
        "summaries": n_sum,
        "briefing": briefing,
        "dispatched": n_disp,
        "mode": "signals" if use_signals else "legacy",
    }
    log.info("daily pipeline done: %s", result)
    return result
