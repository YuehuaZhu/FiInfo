import textwrap
from pathlib import Path

from fiinfo.sources.registry import load_sources, top_stories_config


def _write_cfg(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "sources.yaml"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_loads_enabled_only(tmp_path):
    cfg = _write_cfg(tmp_path, """
        defaults: {enabled: true}
        sources:
          twitter:
            enabled: true
            impl: fiinfo.sources.fixture:FixtureTweetSource
          off_source:
            enabled: false
            impl: fiinfo.sources.fixture:FixtureTweetSource
    """)
    srcs = load_sources(cfg)
    assert len(srcs) == 1


def test_require_env_skips_when_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("NEVER_SET_THIS", raising=False)
    cfg = _write_cfg(tmp_path, """
        sources:
          needs_key:
            enabled: true
            impl: fiinfo.sources.fixture:FixtureTweetSource
            require_env: [NEVER_SET_THIS]
    """)
    srcs = load_sources(cfg)
    assert len(srcs) == 0


def test_import_failure_is_swallowed(tmp_path):
    cfg = _write_cfg(tmp_path, """
        sources:
          broken:
            enabled: true
            impl: fiinfo.nonexistent.module:NopeClass
    """)
    srcs = load_sources(cfg)
    assert len(srcs) == 0  # 没崩,只是跳过


def test_top_stories_config_defaults(tmp_path):
    cfg = _write_cfg(tmp_path, "sources: {}\n")
    ts = top_stories_config(cfg)
    assert ts["enabled"] is False
    assert ts["count"] == 10


def test_top_stories_config_enabled(tmp_path):
    cfg = _write_cfg(tmp_path, """
        sources: {}
        top_stories:
          enabled: true
          count: 7
          llm: qwen
    """)
    ts = top_stories_config(cfg)
    assert ts == {"enabled": True, "count": 7, "llm": "qwen"}
