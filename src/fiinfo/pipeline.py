import logging
from pathlib import Path

from fiinfo.collect import collect_all, collect_signals
from fiinfo.db import init_db
from fiinfo.dispatch import dispatch_today
from fiinfo.render.briefing import render_today, render_today_from_signals
from fiinfo.sources.registry import DEFAULT_CONFIG, load_sources
from fiinfo.summarize_orch import summarize_today, summarize_today_from_signals

log = logging.getLogger(__name__)


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
        briefing = render_today_from_signals()
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
