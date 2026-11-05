# 一条命令把前端发到 Cloudflare Pages
# 用法（在项目根目录）：pwsh -File scripts/deploy-pages.ps1
#
# 如果你不想走浏览器授权，可以先设好 token 再跑：
#   $env:CLOUDFLARE_API_TOKEN = "你的 token"
#   创建地址：https://dash.cloudflare.com/profile/api-tokens（模板选 "Edit Cloudflare Workers"）
# 或直接放一个 secrets 文件（见 docs/deploy.md）。

$ErrorActionPreference = "Stop"
$ProjectName = if ($env:PAGES_PROJECT) { $env:PAGES_PROJECT } else { "flowtable" }

function Find-Wrangler {
  $p = Join-Path $PSScriptRoot "..\node_modules\.bin\wrangler.CMD"
  if (Test-Path $p) { return (Resolve-Path $p).Path }
  $cmd = Get-Command wrangler -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  throw "没找到 wrangler，先在项目根目录跑 pnpm install"
}

$wrangler = Find-Wrangler

Write-Host "==> 1/4 检查环境" -ForegroundColor Cyan
if (-not (Test-Path "node_modules")) { throw "没有 node_modules，先跑 pnpm install" }

Write-Host "==> 2/4 构建静态站" -ForegroundColor Cyan
# CI 只包住构建这一步：wrangler 看到 CI 会拒绝交互式登录，绝不能带出去
$prevCI = $env:CI
$env:CI = "1"
try {
  pnpm --filter @flowtable/web build
  if ($LASTEXITCODE -ne 0) { throw "构建失败，看上面的报错" }
} finally {
  if ($null -eq $prevCI) { Remove-Item Env:CI -ErrorAction SilentlyContinue } else { $env:CI = $prevCI }
}

if (-not (Test-Path "apps\web\dist\index.html")) { throw "构建产物不对：apps\web\dist\index.html 不存在" }

Write-Host "==> 3/4 确认 Cloudflare 登录状态" -ForegroundColor Cyan
$authed = $false

if ($env:CLOUDFLARE_API_TOKEN) {
  Write-Host "检测到 CLOUDFLARE_API_TOKEN，跳过浏览器登录" -ForegroundColor DarkGray
  $authed = $true
} else {
  # 注意：whoami 在未登录时退出码是 0，只能看输出
  $who = (& $wrangler whoami 2>&1 | Out-String)
  if ($who -match "not authenticated|not logged in|You are not authenticated") {
    Write-Host "尚未登录，正在打开浏览器授权（会打开一条 URL，选你的账号 → Allow）..." -ForegroundColor Yellow
    # 双重保险：确保不在 CI 模式
    Remove-Item Env:CI -ErrorAction SilentlyContinue
    & $wrangler login
    if ($LASTEXITCODE -ne 0) {
      throw "登录失败。可以改用 API Token：`$env:CLOUDFLARE_API_TOKEN = '...' 后再跑本脚本"
    }
    $who = (& $wrangler whoami 2>&1 | Out-String)
    if ($who -match "not authenticated|You are not authenticated") {
      throw "登录后仍未通过校验。改用 API Token：`$env:CLOUDFLARE_API_TOKEN = '...'"
    }
  }
  $authed = $true
}

if (-not $authed) { throw "未通过 Cloudflare 认证" }

Write-Host "==> 4/4 部署" -ForegroundColor Cyan
# 项目不存在时创建；已存在会报错，忽略
& $wrangler pages project create $ProjectName --production-branch=main 2>$null | Out-Null

& $wrangler pages deploy apps/web/dist `
  --project-name=$ProjectName `
  --branch=main `
  --commit-dirty=true

if ($LASTEXITCODE -ne 0) { throw "部署失败，看上面的报错" }

Write-Host ""
Write-Host "完成。打开：https://$ProjectName.pages.dev" -ForegroundColor Green
Write-Host "如果这个子域已被占用，上面的输出里会给出实际 URL（形如 $ProjectName-a1b.pages.dev）。" -ForegroundColor Green
Write-Host "下一步：控制台 → 该项目 → Custom domains 绑定自己的域名。" -ForegroundColor Green
