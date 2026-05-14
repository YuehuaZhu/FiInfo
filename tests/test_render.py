from fiinfo.collect import collect_all
from fiinfo.db import init_db
from fiinfo.render.briefing import _md_to_html_basic, render_today
from fiinfo.summarize_orch import summarize_today


def test_md_basic_links_and_lists():
    md = "## DeFi\n- ZK rollups [[z1]](https://x.com/u/z1)\n- another point"
    out = _md_to_html_basic(md)
    assert "<h3>DeFi</h3>" in out
    assert '<a href="https://x.com/u/z1"' in out
    assert "<ul>" in out and "<li>" in out


def test_render_produces_html(tmp_path):
    init_db()
    collect_all(source_name="fixture")
    summarize_today(force_mock=True)
    out = render_today(out_dir=tmp_path)
    html = out.read_text(encoding="utf-8")
    assert out.suffix == ".html"
    assert "<html" in html.lower()
    # 至少一个新类目在 HTML 里(fixture 含 RWA / Stablecoin / PerpDEX / Restaking 等关键词)
    assert any(c in html for c in ("PerpDEX", "Stablecoin", "Restaking", "RWA", "InfraL2"))


def test_dedup_same_url():
    from fiinfo.render.briefing import _dedup_citations_in_line
    line = "- Saylor 观点 [@saylor](https://x.com/saylor/status/1) [@saylor](https://x.com/saylor/status/1)"
    out = _dedup_citations_in_line(line)
    assert out.count("https://x.com/saylor/status/1") == 1


def test_dedup_same_handle_different_urls():
    """同作者多 url 也只保留第一条,避免 @saylor @saylor 重复显示。"""
    from fiinfo.render.briefing import _dedup_citations_in_line
    line = "- 比特币观点 [@saylor](https://x.com/saylor/status/1) [@saylor](https://x.com/saylor/status/2)"
    out = _dedup_citations_in_line(line)
    assert out.count("@saylor") == 1
    assert "status/1" in out  # 第一个保留


def test_dedup_preserves_different_handles():
    from fiinfo.render.briefing import _dedup_citations_in_line
    line = "- 跨人观点 [@saylor](https://x.com/saylor/status/1) [@cz_binance](https://x.com/cz_binance/status/2)"
    out = _dedup_citations_in_line(line)
    assert "@saylor" in out and "@cz_binance" in out
