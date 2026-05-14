"""加载 config/sources.yaml,产出启用的 SignalSource 实例列表。"""
from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from fiinfo.morning_todo import add as todo_add

log = logging.getLogger(__name__)

DEFAULT_CONFIG = Path("config/sources.yaml")

# 把 .env 加载到 os.environ,这样 require_env 检查 os.getenv 才能拿到值
load_dotenv()


def _import(spec: str):
    """'fiinfo.sources.defillama:TVLSource' -> class"""
    mod, _, cls = spec.partition(":")
    return getattr(importlib.import_module(mod), cls)


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_sources(path: Path = DEFAULT_CONFIG) -> list:
    """实例化所有 enabled 的 source。

    缺 require_env 时跳过 + MORNING_TODO 记录,不抛异常。
    实现类导入失败 / 构造失败时同样跳过 + 记录。
    """
    cfg = load_config(path)
    defaults = cfg.get("defaults", {}) or {}
    out: list = []
    for name, spec in (cfg.get("sources") or {}).items():
        merged = {**defaults, **(spec or {})}
        if not merged.get("enabled", True):
            log.debug("source %s disabled", name)
            continue
        missing = [k for k in (merged.get("require_env") or []) if not os.getenv(k)]
        if missing:
            log.warning("source %s skipped: missing env %s", name, missing)
            todo_add(f"启用源 {name} 需配置 env: {', '.join(missing)}")
            continue
        impl = merged.get("impl")
        if not impl:
            log.warning("source %s missing impl, skipped", name)
            continue
        try:
            cls = _import(impl)
            params = merged.get("params") or {}
            inst = cls(**params)
            # 把 registry 里的 name / kind 挂到实例上,源不必接 name 参数
            setattr(inst, "registry_name", name)
            setattr(inst, "kind", merged.get("kind", "?"))
            out.append(inst)
            log.info("source enabled: %s (%s)", name, merged.get("kind", "?"))
        except Exception as e:
            log.warning("source %s failed to load (%s): %s", name, type(e).__name__, e)
            todo_add(f"源 {name} 加载失败: {type(e).__name__}: {e}")
    return out


def top_stories_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """返回 top_stories 全局配置,默认禁用。"""
    cfg = load_config(path)
    ts = cfg.get("top_stories") or {}
    return {"enabled": bool(ts.get("enabled", False)),
            "count": int(ts.get("count", 10)),
            "llm": ts.get("llm", "auto")}
