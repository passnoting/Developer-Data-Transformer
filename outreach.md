# 外联记录表

> 目标：**本周 20 条真实触达，至少 4 个回复，1 笔成交。**
> 规则：每条都要有「对方的原话」。没有原话的记录等于没发生。

---

## 今晚 90 分钟

### Block 1（15 分钟）· 先让钱能进来

- [ ] Creem 注册并**提交**商户申请（审核要几天，现在排队）
- [ ] 同时准备一个**今天就能收钱**的通道：
      - 海外客户：PayPal 收款链接 / 发票
      - 中国客户：微信 / 支付宝
- [ ] 定好两个价：**$49 一次性清表**、**$19/月 代跑**

> 第一单不要等 Creem。收款通道是给第二、第三个客户准备的。

### Block 2（45 分钟）· 找 10 个人，发 5 条

去这些地方，按**最近 7 天**筛选：

| 渠道 | 搜什么 |
|---|---|
| Reddit `r/excel` | `csv`, `duplicate`, `merge`, `encoding` |
| Reddit `r/googlesheets` | `import`, `csv`, `broken` |
| Reddit `r/shopify` | `export`, `report`, `excel` |
| Reddit `r/smallbusiness` | `spreadsheet`, `report takes` |
| Indie Hackers | `manual report`, `csv` |
| 小红书 / 知乎 / 卖家群 | `多平台订单导出`、`订单合并`、`对账` |

**不要发链接。** 先解决他的问题，链接留到他问你"你是做什么的"。

### Block 3（30 分钟）· 填表

把 5 条填进下面的表，写下你发的原文和对方（如果有）的回复。

---

## 模板（直接复制，改一个词就能用）

### EN-1 · Reddit 回帖（最有效）

```
Nine times out of ten this is an encoding issue, not a data issue.

Two culprits:
1) Excel writes UTF-8 with a BOM, and the other tool chokes on it
2) The export is GBK (common on Chinese Windows) and gets read as UTF-8 —
   that's where the  comes from

Paste the first 3 lines and I'll tell you which one it is. If it's quicker,
I'll just clean the file for you — no charge.
```

### EN-2 · 冷邮件 / DM（发给电商运营）

```
Subject: the 40 minutes you spend merging Shopify + Stripe exports

Hi [name] — saw you mention [具体的一句话]. 

I built a small tool that takes the CSV exports you already download and gives
back one clean table: duplicates removed, dates normalised, empty rows gone,
plus a list of every cell it changed. It runs in the browser, nothing uploads.

Is this still a real problem for you, or have you automated it away already?

[link]
```

### EN-3 · 跟进（对方没回，3 天后发一次）

```
Following up once — if the CSV thing is already solved on your side, ignore this.

If it isn't: send me the file (or just the first 3 lines) and I'll clean it and
tell you what was wrong. No charge, no signup.
```

### CN-1 · 跨境卖家群 / 小红书

```
看到你在问多平台订单导出的事。

大概率不是数据问题，是编码问题：从后台/Excel 导出的 CSV 很多是 GBK，
用别的工具打开就变成乱码；还有一种是 UTF-8 带 BOM，第一列名会多一个看不见的字符。

你把前 3 行贴给我，我帮你看是哪种。顺手也能帮你把重复行和日期格式一起清了，
不收钱，我想看看大家是不是都卡在这。
```

### CN-2 · 冷私信（发给做电商/代运营的朋友）

```
在做一个把后台导出的 CSV 自动洗干净的小工具（去重、日期统一、空行清理，
每一步改了什么都列出来）。

你那边每周是不是也要手工拼表？如果有，能不能把一张真实的（脱敏的）表发我，
我跑一遍给你看效果——顺便让我知道真实数据长什么样。
```

---

## 对方回复之后：三段式，不要跳步

**第 1 段 · 问诊**（永远不要先报价）

```
What does it look like when it breaks — extra rows, wrong dates, or columns
that don't line up?
```

中文：`它坏的时候是什么样？多出来的行、日期不对，还是列对不上？`

**第 2 段 · 免费做一次**

拿到文件，用 `flowtable.pages.dev/tools/clean-csv` 跑一遍，把 diff 截图发回去。
这就是你的"演示"，比任何 landing page 都有说服力。

**第 3 段 · 报价**

```
I cleaned it — 3,412 duplicate rows, 17 date formats, 9 empty columns.
Every change is in the sheet, cell by cell.

Two options:
• $49 one-time: I turn this into saved rules you can re-run yourself
• $19/month: it runs every morning at 7am and emails you if the row count looks wrong

No subscription needed for the one-time — the file is already yours.
```

---

## 记录表

| 日期 | 渠道 | 对方（谁/在哪） | 他的原话（关键句） | 我发了什么 | 状态 | 下一步 |
|---|---|---|---|---|---|---|
| 11-05 | r/excel | u/xxx，问合并 CSV | "merging 12 files every month" | EN-1 | 已回复 | 等他发文件 |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

状态用这几个词：`已发` / `已回复` / `给了文件` / `已交付` / `已付费` / `不理我`

---

## 每周日复盘，只回答三个问题

1. 这周发了多少条？**回复率**是多少？
2. 哪一句话的回复率最高？（把原句抄下来，下周只用那一句）
3. 付费的人是在**哪个瞬间**决定付钱的？

---

## 止损线

- **第 30 天**：20 条里回复 < 4 → 改开场白，不改产品
- **第 60 天**：付费 < 3 → 换客户（运营 → 代运营公司 / 会计事务所），不换产品
- **第 90 天**：付费 < 5 且无人续费 → 这个切入点对你不成立

## 明确不做

❌ 改首页文案 ❌ 加功能 ❌ 做另外 4 个工具页 ❌ 买工具 ❌ 投广告
