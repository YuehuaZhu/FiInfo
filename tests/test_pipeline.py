from fiinfo.pipeline import run_daily


def test_run_daily_end_to_end():
    result = run_daily(source_name="fixture", dry_run=True, force_mock_llm=True)
    assert result["briefing"].exists()
    assert result["tweets_collected"] > 0
    assert result["summaries"] >= 1
    assert result["dispatched"] >= 1
    html = result["briefing"].read_text(encoding="utf-8")
    assert "DeFi" in html
