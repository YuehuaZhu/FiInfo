import logging

from fiinfo.collect import collect_all
from fiinfo.db import init_db
from fiinfo.dispatch import dispatch_today
from fiinfo.render.briefing import render_today
from fiinfo.summarize_orch import summarize_today

log = logging.getLogger(__name__)


def run_daily(
    source_name: str | None = None,
    dry_run: bool = True,
    force_mock_llm: bool = False,
) -> dict:
    init_db()
    n_tweets = collect_all(source_name=source_name)
    n_sum = summarize_today(force_mock=force_mock_llm)
    briefing = render_today()
    n_disp = dispatch_today(dry_run=dry_run)
    result = {
        "tweets_collected": n_tweets,
        "summaries": n_sum,
        "briefing": briefing,
        "dispatched": n_disp,
    }
    log.info("daily pipeline done: %s", result)
    return result
