import pytest

from fiinfo.collect import collect_all
from fiinfo.db import init_db
from fiinfo.dispatch import dispatch_today
from fiinfo.publish.dryrun import DryRunPublisher
from fiinfo.publish.twitter import TwitterPublisher
from fiinfo.summarize_orch import summarize_today


def test_dryrun_writes_files(tmp_path):
    p = DryRunPublisher(outbox=tmp_path)
    ids = p.publish_threads([["t1", "t2"], ["other"]])
    assert len(ids) == 2
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_twitter_missing_creds_raises():
    with pytest.raises(RuntimeError):
        TwitterPublisher(consumer_key="", consumer_secret="", access_token="", access_secret="")


def test_dispatch_dryrun_end_to_end(tmp_path):
    init_db()
    collect_all(source_name="fixture")
    summarize_today(force_mock=True)
    n = dispatch_today(dry_run=True, outbox=tmp_path / "outbox")
    assert n >= 1
    files = list((tmp_path / "outbox").glob("*.json"))
    assert len(files) == n
