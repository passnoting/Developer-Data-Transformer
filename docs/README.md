# 项目流程图

三张图，覆盖「系统怎么搭 → 用户怎么买 → 代码怎么发」。

| 图 | 回答的问题 | 格式 |
|---|---|---|
| `01-architecture` | 前端、后端、存储、外部服务各自负责什么，一条管道怎么跑完 | `.png` `.svg` `.drawio` `.mmd` |
| `02-user-journey` | 从一次搜索到一笔订阅，中间有哪些触发点；手工交付这条更快的现金流怎么接 | 同上 |
| `03-release` | 一次 commit 怎么变成客户看到的新数据；迁移、冒烟、监控、回滚在哪一步 | 同上 |

- **`.png`** 直接看、贴进文档
- **`.svg`** 矢量，打印/放大不糊
- **`.drawio`** 用 draw.io 打开可以直接拖拽改
- **`.mmd`** Mermaid，GitHub / Notion / 语雀都能直接渲染

> 所有格式都由 `build_diagrams.py` 生成，**不要手改产物**——改脚本里的 SPEC，再跑一次。

```bash
python docs/build_diagrams.py
```

---

## 一、系统架构（01）

四条泳道，从左到右是数据的流向：

1. **客户端**：免费工具页（SEO 入口，纯静态）→ 应用界面 → 浏览器清洗引擎（同一份 core 跑在 WASM，文件不上传）→ 可选 Chrome 扩展（只做漏斗）。
2. **Edge Worker**：API 路由（Bearer 鉴权）、Cron 调度、管道执行器（fetch → transform → validate → snapshot → alert）、告警器、计费 webhook。
3. **存储**：D1 只放元数据与运行记录（**不存原始数据**）；R2 放最新快照，7 天过期；托管表页 `/t/:token` 是唯一的公开读入口。
4. **外部**：任意 REST/JSON（含 Shopify、Stripe 预置）、Creem（MoR 收款）、Resend（邮件）、客户的 Google Sheets / Excel。

**关键设计**：`托管表页 → 客户的表` 这条边用 `IMPORTDATA` 而不是 Google Sheets API。原因是 Sheets 的 OAuth 验证要 1–3 个月，会卡住上线；用公开只读页 + CSV 下载可以在第一天就跑通交付。

## 二、用户旅程与变现（02）

- **上排（自助）**：搜索长尾词 → 工具落地页 → 免费清洗 → 付费触发点（第 3 次上传 / 想保存规则 / 想每天自动跑）→ 注册。
- **中排（激活与留存）**：建管道 → 首次运行（TTFV < 10 分钟）→ 每日自动刷新 → 行数异常告警 → 升级 Pro。
- **下排（服务化收款）**：社区外联 → 手工交付 $49 → 转 $19/月订阅。

下排不是"备选方案"，而是**最快的现金流**：Product Hunt 被 featured 的第 30 天只有 $531，Show HN 中位 2 分，而手工交付能在 72 小时内收到第一笔钱。下排做三单之后，再决定要不要把中排做深。

## 三、发布与运维（03）

1. 本地 `pnpm dev` / `pnpm dev:api`，核心逻辑用 `pnpm test`（零依赖，node 直接跑 TS）验证。
2. `git push` → **Cloudflare Pages** 自动构建，每个 PR 一个预览 URL。
3. 冒烟检查：工具页能跑、`/api/health` 通。
4. 合并 `main` → 生产 Pages 自动部署。
5. `wrangler deploy` 发布 Worker；`D1 迁移`幂等、先备份。
6. Cron 生效（每日 06:00 全量 / 每小时 Pro）。
7. 监控与自检；异常时：Pages 回退部署、Worker `wrangler rollback`。

**发布纪律**：迁移脚本必须幂等（`CREATE TABLE IF NOT EXISTS`），因为回滚不回滚数据；先备份再跑 `--remote`。
