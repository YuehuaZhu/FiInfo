# FiInfo

Web3 KOL 自动信息采集 → 摘要 → 分发 流水线。

详见 [plan](../../.claude/plans/1-a-cosmic-octopus.md) 与白天待办 [MORNING_TODO.md](MORNING_TODO.md)。

## Quick start

```bash
make install    # uv venv + 依赖 + playwright chromium
make test       # 跑全套单测
make daily      # 端到端跑(fixture + mock LLM + dry-run 发布)
open data/briefing-$(date +%F).html
```
