# FlowTable（工作代号）

**线上：<https://flowtable.pages.dev/>** · 部署方式见 [`docs/deploy.md`](docs/deploy.md) · 上线后行动见 [`docs/launch-checklist.md`](docs/launch-checklist.md)

> **Any API → a clean, always-fresh spreadsheet. No code, no warehouse.**
>
> 把任意 API / JSON / CSV 变成一张每天自动刷新、可校验、每个改动都能追溯的表。

---

## 现在要做什么（v0.1）

只做三件事，其余全部推迟：

| 能力 | 范围 |
|---|---|
| **吸入 Ingest** | CSV 上传（UTF-8 / GBK / UTF-16 自动识别）；任意 REST/JSON（header 鉴权、分页、JSONPath 选根）；Shopify、Stripe |
| **清洗 Clean** | 12 条确定性规则，每条都有预览 + 逐格 diff + 可撤销 |
| **交付 Deliver** | 每日定时 → 托管表页 + CSV 下载 + 邮件；行数异常（±20%）或失败时告警 |

> `.xlsx` 暂不支持上传：它是 ZIP 包，必须先在 Excel/WPS 里「另存为 CSV UTF-8」。现在拖进来会给出明确提示，而不是解出乱码。

**明确不做**：AI 聊天框、100 个集成、图表仪表盘、团队协作、移动端、实时流。

### 两个已经定下来的技术决策

1. **v0.1 不接 Google Sheets API。** OAuth 验证要 1–3 个月（有 8 周卡审的公开案例）。先用托管表页 + `=IMPORTDATA()`，用户 30 秒贴进自己的表；有 20 个付费用户后再去排队。
2. **收款用 Creem**（MoR，3.9% + $0.40，支持支付宝提现，$50 起付）。$19 订阅实收 $18.16，不需要自己处理 VAT。

---

## 目录结构

```
.
├─ apps/
│  ├─ web/                  前端 · Astro 静态站（工具页 + 落地页 + 应用界面）
│  └─ api/                  后端 · Cloudflare Worker（API + Cron + 托管表页）
├─ packages/
│  └─ core/                 清洗引擎（纯 TS，浏览器与 Worker 共用）
├─ infra/
│  └─ d1/schema.sql         D1 表结构
├─ docs/
│  ├─ 01-architecture.*     系统架构与数据流
│  ├─ 02-user-journey.*     用户旅程与变现
│  ├─ 03-release.*          开发 → 发布 → 运维
│  ├─ README.md             三张图的文字说明
│  └─ build_diagrams.py     图表生成脚本（改这张脚本，重出全部格式）
├─ scripts/
│  └─ check-scaffold.mjs    脚手架自检（文件齐不齐、约束破没破）
└─ research/                上一轮市场调研（报告 + 数据）
```

每张图都有 4 种格式：`.png`（直接看）、`.svg`（矢量/打印）、`.mmd`（GitHub 直接渲染）、`.drawio`（可拖拽编辑）。

## 流程图

- [系统架构](docs/01-architecture.png)：四条泳道 + 一条管道的完整链路
- [用户旅程与变现](docs/02-user-journey.png)：搜索 → 免费工具 → 付费墙 → 订阅；以及手工交付这条更快的现金流
- [发布与运维](docs/03-release.png)：commit → Pages 预览 → 生产 → Worker → D1 迁移 → 监控 → 回滚
- [图的文字说明](docs/README.md)：每张图想表达什么、为什么这么画

改图不要改产物，改 `docs/build_diagrams.py` 然后 `python docs/build_diagrams.py`。

---

## 快速开始

前置：**Node ≥ 22**（核心用 node 直接跑 TypeScript）、**pnpm 9**。

```bash
pnpm install          # 首次：拉 astro / wrangler
pnpm test             # 不装依赖也能跑：清洗引擎冒烟测试
pnpm dev              # 前端 http://localhost:4321
pnpm dev:api          # 后端 http://localhost:8787
pnpm db:migrate       # 本地 D1 建表
pnpm db:seed          # 造一个测试 workspace（api_key = dev_key_123）
```

**最快看到东西**：`pnpm dev` → 打开 <http://localhost:4321/tools/clean-csv> → 拖一个带重复行、`2026/11/04`、`$1,234.50` 的 CSV 进去。这个页面完全不依赖后端。

**跑通一条管道**（两个终端：`pnpm dev:api` + 下面的 curl）：

```bash
curl -s -X POST http://localhost:8787/api/pipelines \
  -H "authorization: Bearer dev_key_123" \
  -H "content-type: application/json" \
  -d '{
    "name": "demo-posts",
    "source": { "type": "rest", "url": "https://jsonplaceholder.typicode.com/posts" },
    "rules": [
      { "id": "r1", "type": "trim", "column": "title" },
      { "id": "r2", "type": "dropEmptyRows" }
    ]
  }'
```

返回里带 `tableUrl`，打开就是托管表页；`POST /api/pipelines/<id>/run` 手动跑一次。

## 部署

```bash
wrangler login
wrangler d1 create flowtable            # 把 database_id 填进 apps/api/wrangler.toml
wrangler r2 bucket create flowtable-snapshots
wrangler secret put CREEM_WEBHOOK_SECRET --config apps/api/wrangler.toml
wrangler secret put RESEND_API_KEY --config apps/api/wrangler.toml

pnpm deploy:api       # Cloudflare Workers
pnpm db:migrate:prod  # 生产 D1 建表
pnpm deploy:web       # Cloudflare Pages（静态）
```

---

## 实现状态

| 模块 | 状态 | 说明 |
|---|---|---|
| `packages/core` 规则引擎 | ✅ 可用 | 12 条规则 + diff + 统计，`pnpm test` 可验 |
| `packages/core` 解析/铺平 | ✅ 可用 | CSV 解析（BOM/引号/换行）、JSON 铺平与选根 |
| `apps/api` 路由与执行器 | 🚧 骨架 | `/api/health`、建管道、手动跑、托管表页已通；鉴权与限额是简化版 |
| `apps/api` 定时任务 | 🚧 骨架 | cron 已接，串行执行；管道上千后必须换 Queues |
| `apps/api` 计费 | 🚧 骨架 | Creem webhook 验签 + 订阅状态落库；产品 ID 映射待定 |
| `apps/web` 落地页/工具页 | 🚧 骨架 | 首页与 `clean-csv` 可跑；其余 4 个工具页待补 |
| `apps/web` 应用界面 | ⬜ 未开始 | 管道列表、运行日志、diff 视图 |

标记：✅ 可用 ｜ 🚧 骨架（能跑但缺关键逻辑） ｜ ⬜ 未开始

**上线前必须补的三件事**（现在是有意留白的）：
1. `api_key` 改成 SHA-256 哈希存储（现在明文比对）。
2. 告警去重与重试（同一管道 10 分钟内只发一封）。
3. cron 串行改 Queues（单次 cron 有 CPU 上限，管道一多就会超）。

---

## 设计原则（写代码时用来吵架的）

1. **确定性优先。** 规则必须可预测、可复现、可回滚。AI 只用来**建议规则**，绝不用来**填值**。
2. **文件默认不离开浏览器。** 免费工具全程 WASM 本地处理；服务端只存规则与元数据，快照 7 天自动删除。
3. **按“管道数”计价。** 不按行数、不按 task——这是对“账单不可预测”这条最大差评的直接回应。
4. **失败必须可见。** 任何一次运行，要么写入成功，要么发告警；不允许“绿色面板 + 数据没到”。
