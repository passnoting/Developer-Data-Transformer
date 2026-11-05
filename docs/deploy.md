# 部署到 Cloudflare

分两阶段，**先只做第一阶段**。

第一阶段只发静态站，5 分钟，不需要数据库、不需要信用卡、不需要后端。你现在需要的是一个「能发给别人的链接」，不是一条能跑的管道。

---

## 阶段一：前端上 Pages（今天做）

### 方式 A · 一条命令（推荐）

```powershell
pnpm install          # 如果还没装
pwsh -File scripts/deploy-pages.ps1
```

脚本会依次：构建 → 检查登录（没登录会弹浏览器）→ 创建 Pages 项目 → 上传 `apps/web/dist`。

成功后会打印：

```
https://flowtable.pages.dev
```

### 方式 B · 完全不用命令行

```powershell
pnpm --filter @flowtable/web build
```

然后打开 Cloudflare 控制台 → Workers & Pages → Create → Pages → **Upload assets**，
把 `apps/web/dist` 整个文件夹拖进去。项目名填 `flowtable`。

> 这条路径的好处：不用装 wrangler、不用登录 CLI。缺点是以后每次更新都要手动拖。

### 绑定自己的域名

Pages 项目 → Custom domains → 添加。域名在 Cloudflare Registrar 买的话，DNS 会自动配好，几分钟生效。

绑定后记得改一处，否则 canonical 和 sitemap 里的域名还是 pages.dev：

- Pages 项目 → Settings → Environment variables（Production）加 `SITE_URL=https://你的域名`
- 然后重新部署一次（`pwsh -File scripts/deploy-pages.ps1`）

`astro.config.mjs` 读的就是这个变量，`canonical`、`og:url`、`sitemap.xml` 会一起变——sitemap 是构建时按页面列表生成的，不用手改。

> 如果你暂时用 pages.dev 域名，这一步可以跳过。

### 验证

- [ ] 桌面浏览器打开首页、`/tools/clean-csv`、`/privacy`、`/terms`、随便一个不存在的路径（应看到 404 页）
- [ ] 手机 4G 打开一次
- [ ] 拖一个 GBK 编码的中文 CSV 进 `/tools/clean-csv`，应显示「检测到编码：GB18030」
- [ ] `/sitemap.xml` 能打开，且每个 `<loc>` **以 `/` 结尾**（和页面 canonical 一致）
- [ ] `/robots.txt` 末尾有 `Sitemap: https://.../sitemap.xml`

---

## 阶段二：后端上 Workers（等有人真的要买再做）

前置：`apps/api/wrangler.toml` 里 `database_id = "REPLACE_WITH_D1_ID"` 必须换成真实 ID，否则部署直接失败。

```powershell
# 1) 建数据库，把输出的 database_id 填进 apps/api/wrangler.toml
wrangler d1 create flowtable

# 2) 建快照桶
wrangler r2 bucket create flowtable-snapshots

# 3) 密钥（没有就先不配，代码会降级成打日志）
wrangler secret put CREEM_WEBHOOK_SECRET --config apps/api/wrangler.toml
wrangler secret put RESEND_API_KEY      --config apps/api/wrangler.toml

# 4) 发布 Worker
pnpm deploy:api

# 5) 生产建表（幂等，可重复跑）
pnpm db:migrate:prod

# 6) 验证
curl https://flowtable-api.<你的子域>.workers.dev/api/health
```

期望返回：`{"ok":true,"version":"0.1.0","now":"..."}`

### 接前端

前端目前**不调用**后端（免费工具全在浏览器里跑）。等要做「保存规则 / 每天自动跑」时，
在 Pages 项目里加环境变量 `PUBLIC_API_URL=https://flowtable-api.<你的子域>.workers.dev`。

同时把 `apps/api/wrangler.toml` 的 `APP_URL` 改成你的 Pages 域名——托管表页里的链接和告警邮件都用它。

---

## 常见错误

| 报错 | 原因 | 解决 |
|---|---|---|
| `Project not found` | Pages 项目还没建 | 先 `wrangler pages project create flowtable`（脚本已内置） |
| `Authentication error` | 没登录 / token 过期 | `wrangler login` |
| `In a non-interactive environment, it's necessary to set a CLOUDFLARE_API_TOKEN` | 环境变量里有 `CI`，wrangler 以为在 CI 里 | 清掉：`Remove-Item Env:CI`，再重跑脚本（新版脚本已修） |
| `You are not authenticated` 但脚本没弹登录 | `wrangler whoami` 未登录时退出码仍是 0 | 新版脚本改为匹配输出文本；旧版请手动 `wrangler login` |
| `database_id is not a valid UUID` | 还是占位符 | `wrangler d1 create flowtable` 后填进去 |
| `Could not resolve "..."` | 依赖没装 | `pnpm install` |
| `spawn EPERM` | 有沙箱/杀软拦子进程 | 换普通 PowerShell 窗口跑，不要用受限终端 |
| 上传后 404 | `dist` 目录不对 | 确认 `apps/web/dist/index.html` 存在 |
| 改了文案线上没变 | 浏览器/CDN 缓存 | 已在 `_headers` 里给 HTML 设了 `max-age=0`；硬刷新 Ctrl+F5 |

### 不想走浏览器登录？用 API Token

浏览器授权会卡在「打开 URL 后没回调」的情况（防火墙、公司网络）。这时改用 token：

1. 打开 <https://dash.cloudflare.com/profile/api-tokens>
2. Create Token → 模板选 **Edit Cloudflare Workers** → 权限加上 `Account: Cloudflare Pages: Edit`
3. 复制 token，然后在**同一个终端窗口**里：

```powershell
$env:CLOUDFLARE_API_TOKEN = "粘贴到这里"
pwsh -File scripts/deploy-pages.ps1
```

注意：这个环境变量只在当前窗口有效；关掉窗口就没了，下次要重设。想长期用，写进 `secrets.ps1` 并加进 `.gitignore`。

## 成本

- Pages：免费额度 500 次构建/月，无限带宽（静态）
- Workers：免费 10 万请求/天
- D1：免费 5GB
- R2：免费 10GB

前 100 个用户，Cloudflare 侧应该一直是 $0。唯一的固定支出是域名（约 $10/年）。
