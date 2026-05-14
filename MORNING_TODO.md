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
- [ ] 2026-05-14T17:11:15 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:11:15 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:11:15 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:13:13 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:13:13 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:13:13 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:29:21 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:29:21 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:29:21 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:29:45 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:29:45 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:29:45 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:45:36 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:45:36 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:45:36 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:49:05 — 启用源 twitter 需配置 env: TWITTER_AUTH_TOKEN
- [ ] 2026-05-14T17:49:05 — 源 defillama_tvl 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:05 — 源 defillama_raises 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:05 — 源 defillama_hacks 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:05 — 源 coingecko_trending 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.coingecko'
- [ ] 2026-05-14T17:49:05 — 源 cryptopanic 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.cryptopanic'
- [ ] 2026-05-14T17:49:05 — 源 reddit 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.reddit'
- [ ] 2026-05-14T17:49:05 — 源 snapshot 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.snapshot'
- [ ] 2026-05-14T17:49:05 — 源 github_trending 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.github_trending'
- [ ] 2026-05-14T17:49:05 — 源 rss_zh 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.rss_feeds'
- [ ] 2026-05-14T17:49:05 — 源 rss_en 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.rss_feeds'
- [ ] 2026-05-14T17:49:06 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:49:06 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:49:06 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:49:23 — 启用源 twitter 需配置 env: TWITTER_AUTH_TOKEN
- [ ] 2026-05-14T17:49:23 — 源 defillama_tvl 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:23 — 源 defillama_raises 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:23 — 源 defillama_hacks 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.defillama'
- [ ] 2026-05-14T17:49:23 — 源 coingecko_trending 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.coingecko'
- [ ] 2026-05-14T17:49:23 — 源 cryptopanic 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.cryptopanic'
- [ ] 2026-05-14T17:49:23 — 源 reddit 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.reddit'
- [ ] 2026-05-14T17:49:23 — 源 snapshot 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.snapshot'
- [ ] 2026-05-14T17:49:23 — 源 github_trending 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.github_trending'
- [ ] 2026-05-14T17:49:23 — 源 rss_zh 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.rss_feeds'
- [ ] 2026-05-14T17:49:23 — 源 rss_en 加载失败: ModuleNotFoundError: No module named 'fiinfo.sources.rss_feeds'
- [ ] 2026-05-14T17:49:23 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T17:49:23 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T17:49:23 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T17:50:02 — 启用源 twitter 需配置 env: TWITTER_AUTH_TOKEN
- [ ] 2026-05-14T19:08:31 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T19:08:31 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T19:08:31 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T19:12:09 — DefiLlama /raises 请求失败: HTTPStatusError: Client error '402 Payment Required' for url 'https://api.llama.fi/raises'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/402
- [ ] 2026-05-14T19:13:40 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T19:13:40 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T19:13:40 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T19:31:18 — Reddit /r/CryptoCurrency 失败: HTTPStatusError
- [ ] 2026-05-14T19:31:20 — Reddit /r/ethfinance 失败: HTTPStatusError
- [ ] 2026-05-14T19:31:40 — Reddit /r/solana 失败: ConnectTimeout
- [ ] 2026-05-14T19:31:42 — Reddit /r/defi 失败: HTTPStatusError
- [ ] 2026-05-14T19:33:14 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T19:33:14 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T19:33:14 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T20:01:54 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T20:01:54 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T20:01:54 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T20:03:38 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T20:03:38 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T20:03:38 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取

## 2026-05-14 Phase 9 继续推进未完成项 - 探测结果

### 已自动启用(本轮新增)
- ✅ Reddit:用 `.rss` atom feed 走通(JSON 端点 2024 后封禁),5 个 sub × 15 帖
- ✅ 英文 RSS 扩充到 6 个源:CoinTelegraph / The Block / Decrypt / CoinDesk / DL News / Bitcoinist

### 探测后确认拿不到,等用户介入
- ❌ **中文 RSS** - foresightnews/odaily/chaincatcher/8btc/jinse/panews/theblockbeats 全关 RSS 改 SPA;RSSHub 公共实例 (rsshub.app) 403
  - **解决方案 A**:你提供一个自建 RSSHub URL(GitHub: DIYgod/RSSHub,自部署 docker 一键起)
  - **解决方案 B**:你提供 Telegram 频道 ID + bot token,系统转 Telegram 公开频道为信号源
  - **解决方案 C**:接受英文为主,放弃中文 RSS
- ❌ **TokenUnlocks** - 公开 API 改私有(tokenomist.ai 重定向到 SPA),DefiLlama emissions 也付费了
  - 等待出现新的公开 unlock 日历 API,或用户付费(~$30/月 Token Terminal)
- ❌ **CryptoPanic** - Cloudflare 403。需要 `CRYPTOPANIC_TOKEN`(免费 100/day, https://cryptopanic.com/developers/api/)
- ❌ **DefiLlama Raises** - 转付费 Pro API(~$300/月)
- ❌ **Etherscan Whales** - 需要 `ETHERSCAN_KEY`(免费 5 req/s, https://etherscan.io/myapikey)
- [ ] 2026-05-14T20:52:40 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T20:52:40 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T20:52:40 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T21:05:44 — DefiLlama /protocols 请求失败: ConnectTimeout: _ssl.c:993: The handshake operation timed out
- [ ] 2026-05-14T21:06:14 — DefiLlama /hacks 请求失败: ConnectTimeout: _ssl.c:993: The handshake operation timed out
- [ ] 2026-05-14T21:06:34 — CoinGecko trending 请求失败: ConnectTimeout: _ssl.c:993: The handshake operation timed out
- [ ] 2026-05-14T21:06:49 — Reddit /r/CryptoCurrency 失败: ConnectTimeout
- [ ] 2026-05-14T21:07:04 — Reddit /r/ethfinance 失败: ConnectTimeout
- [ ] 2026-05-14T21:46:49 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T21:46:49 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T21:46:49 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T21:53:21 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T21:53:21 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T21:53:21 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
- [ ] 2026-05-14T21:59:21 — 启用源 needs_key 需配置 env: NEVER_SET_THIS
- [ ] 2026-05-14T21:59:21 — 源 broken 加载失败: ModuleNotFoundError: No module named 'fiinfo.nonexistent'
- [ ] 2026-05-14T21:59:21 — 配置 TWITTER_AUTH_TOKEN(浏览器 cookie auth_token)以启用真实抓取
