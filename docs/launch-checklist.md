# 上线清单（从「写完代码」到「收到钱」）

> 规则：**这 4 周不写新功能。** 除了修 bug，所有时间花在「让人用」和「收钱」上。
> 每完成一项就打勾，卡住超过半天就在群里问，别自己憋。

---

## D0 · 让它存在于公网（约 2 小时）

- [ ] 买域名（Cloudflare Registrar 成本价，约 $10/年）
- [ ] `pnpm install && pnpm build`
- [ ] `wrangler pages deploy apps/web/dist --project-name=flowtable`
- [ ] 在 Pages 里绑定域名，等 DNS 生效
- [ ] 手机打开一次，确认 4G 网络下也能用
- [ ] Google Search Console 添加站点，提交 `sitemap.xml`

**验收**：把这个链接发给一个陌生人，他能自己看懂是干什么的。

> 这一步**不需要后端**。免费工具页是纯静态的，先上线，再谈管道。

## D1 · 让它可信（约 2 小时）

- [ ] 填掉 `privacy.astro` / `terms.astro` 里的方括号：`[CONTACT EMAIL]`、`[YOUR LEGAL ENTITY]`、`[JURISDICTION]`、`[DATE]`
- [ ] 页脚邮箱改成真实可收信的地址
- [ ] 加一页 `/about`：你是谁、为什么做这个、一张真人照片
      （真实姓名 + 照片对转化的影响，远大于任何文案优化）
- [ ] 首页底部放一句「有问题直接发邮件给我」，而不是表单

**验收**：你自己点一遍 Privacy / Terms / 404，没有 404 链、没有占位符。

## D2–D3 · 让它能收钱（约 4 小时）

- [ ] 注册 Creem（MoR，3.9% + $0.40，支持支付宝提现）
- [ ] 建两个产品：
      - `One-time cleanup` **$49**（人工交付：你帮他清一次表 + 固化规则）
      - `Starter` **$19/月**（3 条管道、每日刷新、邮件告警）
- [ ] 用 Creem 的 **Payment Link**，不要先写 checkout 代码
- [ ] 定价页按钮指向 payment link
- [ ] **自己买一次**，走完支付 → 回调 → 收据全流程

**验收**：一笔真实扣款成功，你收到了钱（哪怕 $1 测试价）。

## D4–D7 · 找 20 个人（每天 5 条，共约 3 小时）

在哪找（按命中率排序）：

1. Reddit：`r/excel`、`r/googlesheets`、`r/smallbusiness`、`r/shopify` 里搜
   `csv`、`merge`、`duplicate`、`export`、`zapier broke`，找**最近 7 天**的提问
2. Indie Hackers / r/SaaS 里抱怨「report takes 3 hours」的人
3. 你认识的、在小公司做运营/财务的人（最容易成交，别跳过）

怎么发（**不要贴链接**）：

```
Saw your post about the duplicated rows. Nine times out of ten it's an
encoding/BOM issue rather than a data issue — Excel writes UTF-8 with a BOM
and the other tool chokes on it.

If you paste the first 3 lines here (or DM me), I'll tell you which rule is
failing. I do this a lot; happy to just clean it for you, no charge.
```

- [ ] D4：5 条
- [ ] D5：5 条
- [ ] D6：5 条
- [ ] D7：5 条 + 复盘哪句话有人回

**验收**：≥ 4 个回复，≥ 2 个人愿意把文件发给你。

## 第 2 周 · 交付 3 单

- [ ] 用现有的工具 + 手工，帮他们清完（不要等产品功能）
- [ ] 交付物：干净的表 + 一份「我改了什么」的清单（这正是 `diff` 的用途）
- [ ] 交付后报价：**$49 一次性固化规则**，或 **$19/月帮你每天跑**
- [ ] 每一单都问一句：「如果不做这个，你原来打算怎么办？」（答案就是你的文案）

**验收**：至少 1 笔 $49 到账。到账前不要写任何新功能。

## 第 3 周 · 把重复出现的需求做成产品

只有当**至少 3 个人提出同一个需求**时才动手：

- [ ] 统计 3 单里重复出现的动作（大概率是：定时、校验规则、告警）
- [ ] 只做那一个，其余全部拒绝
- [ ] 把 3 个真实案例写成 case study（用他们的话，不要用你的形容词）

## 第 4 周 · 复盘

回答三个问题，写下来：

1. 20 条触达里，回复率是多少？哪句话的回复率最高？
2. 付费的人，是在哪个瞬间决定付钱的？
3. 没付费的人，卡在哪一句？

然后决定：继续、换 ICP、还是换方向。

---

## 每周只盯 3 个数字

| 指标 | 目标 | 说明 |
|---|---|---|
| 本周新增真实对话 | ≥ 5 | 不是「曝光」，是有人回你 |
| 免费工具被使用次数 | 记录基线即可 | 第 4 周才用它判断 SEO 值不值得投 |
| 付费笔数 | W2 起 ≥ 1 | 金额不重要，有没有人掏钱最重要 |

## 止损线（写在日历上）

- **第 30 天**：20 条触达回复 < 4 → 改开场白，不改产品
- **第 60 天**：付费 < 3 → 换客户（从「运营」换到「代运营公司 / 会计事务所」），不要换产品
- **第 90 天**：付费 < 5 且无人续费 → 这个切入点对你不成立，回调研报告里选第 3 名

## 明确不做（这 4 周）

- ❌ 继续写 xlsx 解析、应用界面、另外 4 个工具页
- ❌ 做 Google Sheets 插件（审核 1–3 个月，等有 20 个付费用户再说）
- ❌ Product Hunt / Show HN（预期是 100–800 访客、$0–2 付费，不是增长引擎）
- ❌ 买任何工具、投任何广告
