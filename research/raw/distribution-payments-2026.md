# 独立开发者卖 SaaS 给英语市场：分发渠道与收款真实数据（2026-11）

## 1. Chrome Web Store（重点）

| 项 | 事实 | 来源 |
|---|---|---|
| 注册费 | 一次性 registration fee（无年费）。官方文档只写"one-time…fee"，未标金额；$5 见开发指南 | [register 文档 2023-08-02](https://developer.chrome.com/docs/webstore/register)、[实践指南](https://github.com/marcusquinn/aidevops/blob/main/.agents/browser-extension-dev/publishing.md) |
| 审核时长 | 官方：2021 年初多数 <24h，90%+ 在 3 天内；超 3 周可找支持。新开发者/新扩展/敏感权限/大改代码更慢 | [review process](https://developer.chrome.com/docs/webstore/review-process) |
| 远程代码禁令 | MV3 下逻辑必须自包含；禁 `<script>` 外链、`eval()`、远程解释器；审查看不出完整功能即拒 | [MV3 附加要求 2022-11-01](https://developer.chrome.com/docs/webstore/program-policies/mv3-requirements) |
| 其他政策 | 单一用途、隐私政策、数据使用披露；**提供付费功能者必须填真实物理地址** | [policies](https://developer.chrome.com/docs/webstore/program-policies)、[set-up-account 2023-10-16](https://developer.chrome.com/docs/webstore/set-up-account) |
| 商店内收款 | **已死**。2020-09-21 停止新建付费项；**2021-02-01 起 CWS Payments 不再收钱**，licensing API 之后也会关 | [CWS payments deprecation 2020-09-20](https://developer.chrome.com/docs/webstore/cws-payments-deprecation) |
| 现在怎么收钱 | 只能自建：Stripe/Paddle 结账页 + 自己发 license key（ExtensionPay 等第三方壳也走这条路） | 同上（官方要求"migrate to another payments processor"） |
| 扩展总数 | **unknown**。Google 不公布；2020 年第三方口径 137,345 未能复核 | — |
| 安装分布 | 官方明说 "Users" 统计**安装量、不追踪活跃** | [metrics 文档](https://developer.chrome.com/docs/webstore/metrics) |
| 精选位 | 官方称会 "robustly curate" 商店，但无公开申请标准/名额 → 难度 **unknown（高）** | policies 同上 |

收入分布没有权威中位数：2026-03 的行业分析明确写"无可靠 median income"，能引用的只有个案——GMass 2019-01 $115k/月、Closet Tools 2020-12 $38k/月（[Chrome Goldmine 2026-03-26](https://chromegoldmine.com/blog/chrome-extension-monetization/chrome-extension-revenue-benchmarks/)）。模型推演：1,000 活跃 ×2% 付费 ×$10 = **$200/月**。

## 2. Google Workspace Marketplace（CSV/Excel 方向关键渠道）

| 项 | 事实 |
|---|---|
| 上架费 | 免费。需 GCP 项目 + OAuth consent + Marketplace SDK + listing |
| 门槛 | 自有域名（Search Console 验证所有权）、隐私政策、Terms；restricted scope 要演示视频 + 逐条 scope 说明（[发布指南](https://developers.google.com/workspace/marketplace/how-to-publish)、[实操记录](https://gist.github.com/imthenachoman/6cff4a1170390f01c15d4da87110124a)） |
| 审核时长 | **数周至数月**，官方无 SLA。实名案例：2025-10-31 提交、2026-01 仍卡在 OAuth 验证（[论坛 2026-01-07](https://discuss.google.dev/t/oauth-verification-for-workspace-add-on-stuck-for-8-weeks-client-critical/318451)）；另有 ~12 周案例（2026-08） |
| 收费 | add-on **无内建内购**；Chrome Web Store 付费通道关停后，Sheets/Drive add-on 只能自建订阅（Stripe 等）。"Google Cloud 计费/经销商"路径适用于部分 Marketplace 应用，add-on 侧是否可用 **unknown** |
| 分发价值 | 用户就在表格里、意图极强、免广告费；缺点是审核慢 + 命名受 Google 商标规则约束 |
| 案例 | Coefficient（Sheets/Excel 原生 add-on，2022-11 拿 $18M Series A，[BusinessWire](https://www.businesswire.com/news/home/20221109006158/en/)）；Supermetrics 以报表连接器起家（一手来源未核验 → **unknown**） |

风险：restricted scope 可能触发年度 CASA 安全评估（费用/是否强制 **unknown**，需按 scope 逐个确认）。

## 3. 渠道对比

| 渠道 | 上架费 | 审核 | 抽成 | 强制店内支付 | 独立开发者可上榜 | 量级 |
|---|---|---|---|---|---|---|
| Chrome Web Store | $5 一次性 | 1–3 天（敏感权限更久） | 0%（无支付） | 否，必须自建 | 是（但难被发现） | 极大 |
| Workspace Marketplace | $0 | 数周–数月 | 0% | 基本自建 | 是（类目小） | 中 |
| VS Code Marketplace | $0 | 分钟–数天 | 0% | 否 | 是 | 大（开发者） |
| GitHub Marketplace | $0 | 数天–数周 | **unknown** | 部分 | 难 | 中 |
| Slack App Directory | $0 | 严格、数周 | 0% | 否（Slack 不收款） | 难 | 中 |
| Shopify App Store | $0 | 数天–数周 | **首 $1M 终身 0%，超出 15%**（2025-06-16 生效） | **是**（Billing API） | 是 | 16,000+ 应用（[changelog 2025-04-24](https://shopify.dev/changelog/posts/update-to-shopifys-app-developer-revenue-share)） |
| Atlassian Marketplace | $0 | 数天–数周 | 15%（Cloud）/25%（DC）**待官方页复核** | 是 | 中 | 中 |
| Microsoft AppSource | $0 | 数周 | transact 约 3%（Azure 口径） | 部分 | 难 | 中 |
| WordPress.org | $0 | 数天–数周 | 0% | 否 | 是 | 极大 |
| Product Hunt | $0 | 当天 | 0% | 否 | 是（约 10% 能上首页） | 脉冲 |
| Show HN | $0 | 无 | 0% | 否 | 是（中位 2 分） | 脉冲 |

## 4. 收款：月收入 $1,000 实收（假设 10 笔 $100、跨境卡订阅）

| 通道 | 费率 | MoR 代缴税 | 实收 | 备注 |
|---|---|---|---|---|
| Stripe | 2.9%+$0.30，国际卡 +1.5% | ❌ 自己报 | **≈$953** | 需海外实体+银行账户；中国大陆不可直接开 |
| Paddle | 5%+$0.50 | ✅ | **≈$945** | 需审核站点 |
| Lemon Squeezy | 5%+$0.50 | ✅ | **≈$945** | 已是 Stripe 公司，2026 转向 Stripe Managed Payments（[定价页](https://www.lemonsqueezy.com/pricing)、[2026 公告](https://www.lemonsqueezy.com/blog/2026-update)） |
| Polar | 5%+$0.50（2026-05-27 后新组织）+1.5% 国际卡 | ✅ | **≈$930** | [官方 fees](https://polar.sh/docs/merchant-of-record/fees) |
| Creem | 3.9%+$0.40 | ✅ | **≈$950**（扣 $7 提现费后） | [官方文档](https://docs.creem.io/getting-started/introduction) |
| Gumroad | 10%（2026 未复核 → **unknown**） | 部分 | ≈$900 | — |

- **提现到中国**：Creem 明确支持——个人 Alipay 单笔 ≤5 万 CNY、年 30–60 万 CNY；企业走本地银行不限额；起付 **$50**，每月 1/15 日打款（[payouts 文档](https://docs.creem.io/merchant-of-record/finance/payouts)）。其他家中国提现 **unknown**。
- **税务最低成本路径**：直接用 MoR（Creem/Paddle/LS/Polar）——它替你注册、计算、申报 VAT/GST/sales tax，你只报本国收入。$0-100 预算下这是唯一可行路径；Stripe 路线要自己处理 EU OSS/UK/US 州税，成本远超预算。

## 5. 冷启动真实数据

| 渠道 | 可核验数据 |
|---|---|
| Product Hunt | 2024 起编辑策展，约 10% 上首页；featured 日访 1k–5k、#1 为 5k–10k+、未 featured 仅 100–500；注册率 1–3%；Day2 流量跌到 Day1 的 20–36%。案例：某 featured #6，Day30 = 9 客户 / **$531**；own.page #2 得 17,300 访 / 2,021 注册（[VisitTrack 2026-10-01 汇总](https://visitrack.app/blog/how-to-measure-product-hunt-launch)） |
| Show HN | 188,085 帖全量分析：**中位 2 分**，50 分 = top 6%，250 分 = top 1%；2025 年 28,302 帖（≈200/天）；HN 1 分 ≈ 1.4 GitHub star，半衰期 24h，48h 后 92% 效果结束（[2026-04-23](https://danfking.github.io/blog/2026/04/23/show-hn-by-the-numbers/)） |
| SEO | Ahrefs 2025-05：100 万新 URL 中仅 **1.74%** 一年内进前 10；英文过滤后 6.11%；top10 页面 73% 超 3 年，平均 #1 页面 5 年（[原研究](https://ahrefs.com/blog/how-long-does-it-take-to-rank-in-google-and-how-old-are-top-ranking-pages/)）→ 新站 6–12 个月才见量 |
| Reddit | 封禁/降权风险真实但无公开量化 → **unknown**（自荐链接易被判 spam） |
| programmatic SEO | 本次未取到可核验的成败数据集 → **unknown**，不给数字 |

## 6. 结论：$100 预算、单人、要"第一批付费用户"

按 ROI 排序：
1. **Workspace Marketplace（Sheets add-on）**：免费、意图最准、CSV/Excel 用户就在表格里。代价是 1–3 个月审核——把它当"3 个月后到账的渠道"，同时用落地页承接。
2. **Chrome 扩展当漏斗入口，不当收入来源**：$5 上架，扩展做"导出/抓取"这一小步，付费动作引导到自己站点（因为店内无法收款）。
3. **垂直社区/直接外联**（Reddit 细分版、Indie Hackers、行业 Slack）：零成本、可当天拿到前 3 个付费用户；风险是封禁，用"先答后卖"。
4. **Product Hunt 打一次**：$0，期望值 5–20 注册 / 几百美元，当作 backlink + 徽章，不是增长引擎。
5. **SEO/内容**：$0 现金但 6–12 个月，只在前 4 条跑起来后投入。

**看起来美好但实际无效的陷阱**：把 PH/Show HN 冲榜当渠道（中位 2 分、24h 衰减）；"上架商店就有自然流量"（商店策展 + 无支付）；Apple/Google 应用商店（30% 抽成 + 审核，$100 预算不该碰）；AppSumo 终身 deal（拿现金流换掉未来 ARR）。

**"做个 Chrome 扩展上架就能赚钱"——2026 年不成立。** 依据：① 商店内支付 2021-02-01 已关闭，你必须自建 billing + license，这是额外工程量而非"上架即收钱"；② 官方承认安装量≠活跃，1,000 活跃 ×2% ×$10 ≈ $200/月，是"有用户"而非"有收入"；③ 没有官方收入中位数，能引用的成功案例都是 2019–2020 年的 GMass/Closet Tools 量级，且已被 SEO/联盟站复制；④ 头部位置被 Grammarly、Honey、Capital One Shopping 等公司产品占据（具体榜单未核验 → 定性判断）。扩展在 2026 年的正确定位是**获客漏斗**，不是收银台。

---

### 自评：哪些事实有 URL 支撑

**强支撑（读到原文）**：CWS 支付关停时间线（2020-09-20 官方页，含 2020-09-21/2021-02-01 两个日期）；MV3 远程代码禁令条文；CWS 审核时长口径与"付费功能需物理地址"；CWS "Users=安装量"；Shopify 0%/15% 与生效日 + 16,000 应用；Lemon Squeezy 5%+50¢ 与 Stripe 关系；Polar 全量费率表；Creem 3.9%+40¢、$50 起付、中国 Alipay 限额；Show HN 全量统计；Ahrefs 2025-05 的 1.74%/6.11%/5 年；PH 流量与 $531 案例；Workspace add-on 实操门槛与 8 周 OAuth 卡审案例。

**弱支撑**：$5 注册费（官方页只写 one-time fee，金额来自开发指南）；Paddle 5%+50¢（官网 JS 未取到文本，靠二手交叉）；Atlassian 15%/25%、Gumroad 10%、AppSource 3%、GitHub 抽成（未能打开官方页）；Supermetrics 起源。

**明确 unknown**：CWS 扩展总数与收入中位数；CWS 精选位标准；Workspace add-on 是否可走 Google Cloud 计费；中国提现（除 Creem 外）；Reddit 封禁量化；programmatic SEO 成败数据；Top 扩展榜单构成。以上均未编造。
