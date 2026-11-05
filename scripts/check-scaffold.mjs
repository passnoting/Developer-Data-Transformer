#!/usr/bin/env node
/**
 * 脚手架自检：不跑构建，只确认关键文件在、关键约束没被破坏。
 * `pnpm check` 会先跑 core 的冒烟测试，再跑这个。
 */
import { existsSync, readFileSync } from "node:fs";

const REQUIRED = [
  "README.md",
  "package.json",
  "pnpm-workspace.yaml",
  "tsconfig.base.json",
  "packages/core/src/index.ts",
  "packages/core/src/rules.ts",
  "packages/core/src/engine.ts",
  "packages/core/src/flatten.ts",
  "packages/core/src/csv.ts",
  "apps/api/src/index.ts",
  "apps/api/src/runner.ts",
  "apps/api/wrangler.toml",
  "apps/web/astro.config.mjs",
  "apps/web/src/pages/index.astro",
  "apps/web/src/pages/tools/clean-csv.astro",
  "infra/d1/schema.sql",
  "docs/README.md",
  "docs/01-architecture.png",
  "docs/02-user-journey.png",
  "docs/03-release.png",
];

let failed = 0;
for (const f of REQUIRED) {
  if (!existsSync(f)) {
    console.error(`✗ 缺文件：${f}`);
    failed++;
  }
}

// 约束：schema 必须幂等（回滚不回滚数据，重复执行不能报错）
const schema = readFileSync("infra/d1/schema.sql", "utf8");
const creates = schema.match(/CREATE TABLE/gi)?.length ?? 0;
const idempotent = schema.match(/CREATE TABLE IF NOT EXISTS/gi)?.length ?? 0;
if (creates !== idempotent) {
  console.error(`✗ infra/d1/schema.sql 有 ${creates - idempotent} 个非幂等的 CREATE TABLE`);
  failed++;
}

// 约束：worker 的 wrangler.toml 必须绑定 D1 与 R2
const wrangler = readFileSync("apps/api/wrangler.toml", "utf8");
for (const binding of ["[[d1_databases]]", "[[r2_buckets]]", "binding = \"DB\"", "binding = \"SNAPSHOTS\""]) {
  if (!wrangler.includes(binding)) {
    console.error(`✗ wrangler.toml 缺少：${binding}`);
    failed++;
  }
}

// 约束：免费工具页不得引用后端 API（文件不上传的承诺）
const toolPage = readFileSync("apps/web/src/pages/tools/clean-csv.astro", "utf8");
if (/fetch\(\s*["'`]http/.test(toolPage)) {
  console.error("✗ 免费工具页出现了远程请求，破坏「文件不上传」的承诺");
  failed++;
}

if (failed > 0) {
  console.error(`\n${failed} 项检查未通过`);
  process.exit(1);
}
console.log("✅ scaffold check passed");
