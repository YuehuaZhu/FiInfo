# FiInfo

Web3 KOL 自动信息采集 → LLM 二次摘要 → 自动分发流水线。每日凌晨抓取 → 生成单页 HTML 简报 → 早晨双击查看。

## Quick start

```bash
make install                # uv venv + 依赖 + playwright chromium
make test                   # 19 个测试 / 覆盖率 86%
make daily                  # 端到端跑(fixture 数据 + mock LLM + dry-run 发布)
open data/briefing-$(date +%F).html
```

## 三阶段流水线

1. **采集** — `TweetSource`(`FixtureTweetSource` mock / `PlaywrightTweetSource` 占位骨架)抓取 Top N% KOL 推文,写入 SQLite。
2. **摘要** — `Summarizer`(`EchoSummarizer` mock / `ClaudeSummarizer` 真 LLM),按类目生成 Markdown,保留 `[[tweet_id]](url)` 出处。
3. **分发** — `Publisher`(`DryRunPublisher` 写本地 outbox / `TwitterPublisher` 真发推)。

## 目录

```
src/fiinfo/         核心包(config/db/models/collect/categorize/summarize/render/publish/dispatch/pipeline/cli)
seeds/              KOL 种子(初始 30 条 × 4 类目)
fixtures/           Mock 推文数据
tools/ask_user.py   30s 超时交互助手(/goal 无人值守用)
tests/              pytest
deploy/             systemd timer + VPS 部署文档
MORNING_TODO.md     /goal 模式累积的待用户处理项
```

## 占位 / 降级策略

任何外部凭据缺失,程序自动降级,不会卡住:

| 缺失 | 行为 |
|------|------|
| `TWITTER_AUTH_TOKEN` | 切 `FixtureTweetSource`,记一条 MORNING_TODO |
| `ANTHROPIC_API_KEY` | 切 `EchoSummarizer`(截 160 字 + 保留链接) |
| Twitter 写凭据 | 切 `DryRunPublisher`,thread JSON 写到 `data/outbox/` |

## 白天醒来要做的事

请打开 [MORNING_TODO.md](MORNING_TODO.md) —— 所有 /goal 通宵期间需要你介入的事项都在这。

## 部署

见 [deploy/README.md](deploy/README.md)。
