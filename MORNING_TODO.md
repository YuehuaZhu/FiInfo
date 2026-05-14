# Morning TODO — 等用户白天处理

> /goal 模式通宵执行完成。下面分两栏:**必须用户介入** 与 **建议增强**。

## 必须用户介入(系统才能从 mock 切到真实)

- [ ] 注册或提供 Twitter 账号 cookie `auth_token`,填入 `.env` 的 `TWITTER_AUTH_TOKEN`(否则一直走 fixture)
- [ ] 提供 `ANTHROPIC_API_KEY`(否则继续 `EchoSummarizer` 简单截断摘要)
- [ ] (可选)申请 Twitter 写权限 OAuth1.1 四个 key,填入 `.env`(缺则一直 DryRun 写 `data/outbox/*.json`)
- [ ] 准备 1C2G VPS,按 [deploy/README.md](deploy/README.md) 部署

## 建议增强(白天和 Claude 一起做)

- [ ] 扩充 `seeds/kol_seed.csv` 到 200+ KOL(目前 30 条手工 × 4 类目)
- [ ] 实现 `src/fiinfo/sources/playwright_src.py` 真实抓取(cookie 注入 + scroll + DOM parse + 代理池)
- [ ] 给 `categorize.py` 加关键词覆写,避免 KOL 跨类目(如 elonmusk 同时聊 AI 和加密)
- [ ] 渲染模板美化:暗黑模式 / 移动端 / 图表
- [ ] 接入飞书 MCP,把每日简报同步到飞书文档
- [ ] 给 Twitter 真发推接入 OAuth2 PKCE(tweepy 已支持)
- [ ] 增加 RSS / Mirror / Farcaster 等其他数据源,继承 `TweetSource`

## /goal 期间自动累计的运行时记录

(下面行由 `tools/ask_user.py` 与 `morning_todo.add()` 在测试 / 实际跑时自动追加,不必逐条处理,只要上面"必须用户介入"清单做完就行)

- [ ] 2026-05-14 跑 `pytest` 多次触发 `PlaywrightTweetSource` 构造,均因 no cookie 落入 TODO
- [ ] 2026-05-14T08:06:59 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T11:39:19 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T11:42:12 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T14:20:20 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T14:20:46 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T15:01:59 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T15:12:47 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T15:13:22 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取

## /goal 期间累计

- [ ] 2026-05-14 豆包接入代码已就位,但 agora-v4 上 jack/tom/alice 两个 ARK key 都 AccountOverdue(403),需要你提供一个充值过的 ARK_API_KEY 或自己开个新账号(火山方舟控制台领 200 万 token/天免费额度)
- [ ] 2026-05-14T16:59:07 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:01:00 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
