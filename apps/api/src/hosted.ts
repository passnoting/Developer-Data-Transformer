import type { Dataset } from "@flowtable/core";
import type { SnapshotMeta } from "./types.ts";

const escapeHtml = (v: unknown): string =>
  String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const fmt = (n: number): string => new Intl.NumberFormat("en-US").format(n);

/**
 * 托管表页：一个公开的只读快照页。
 *
 * 为什么不用 Google Sheets API：OAuth 验证要 1–3 个月。
 * 用户把这页的地址喂给 `=IMPORTDATA("...")` 就能贴进自己的表，
 * 或者直接点“下载 CSV”。等有 20 个付费用户再去排队接 Sheets。
 */
export function renderHostedPage(meta: SnapshotMeta, dataset: Dataset, csvPath: string): string {
  const shown = dataset.rows.slice(0, 500);
  const head = dataset.columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const body = shown
    .map(
      (row) =>
        `<tr>${dataset.columns
          .map((c) => `<td>${escapeHtml(row[c])}</td>`)
          .join("")}</tr>`,
    )
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>${escapeHtml(meta.name)} · FlowTable</title>
<style>
  :root{--line:#e3e6ea;--ink:#15181d;--muted:#6b7480}
  *{box-sizing:border-box}
  body{margin:0;font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fff}
  header{padding:20px 24px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:12px;align-items:baseline}
  h1{font-size:18px;margin:0}
  .meta{color:var(--muted);font-size:12.5px}
  .actions{margin-left:auto;display:flex;gap:10px}
  a.btn{border:1px solid var(--line);border-radius:7px;padding:6px 12px;text-decoration:none;color:var(--ink);font-size:13px}
  a.btn:hover{background:#f7f8fa}
  .warn{margin:0;padding:10px 24px;background:#fff7ed;border-bottom:1px solid #fed7aa;color:#9a3412;font-size:13px}
  .wrap{overflow:auto;max-height:calc(100vh - 140px)}
  table{border-collapse:collapse;width:100%;font-size:13px}
  th,td{border-bottom:1px solid var(--line);padding:8px 12px;text-align:left;white-space:nowrap}
  th{position:sticky;top:0;background:#f3f5f9;font-weight:600}
  tbody tr:hover{background:#fafbfd}
  footer{padding:12px 24px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
</style>
</head>
<body>
<header>
  <h1>${escapeHtml(meta.name)}</h1>
  <span class="meta">${fmt(meta.rowsOut)} rows · updated ${escapeHtml(meta.updatedAt.replace("T", " ").slice(0, 16))} UTC</span>
  <div class="actions">
    <a class="btn" href="${escapeHtml(csvPath)}">Download CSV</a>
    <a class="btn" href="/">FlowTable</a>
  </div>
</header>
${meta.warnings.length ? `<p class="warn">${meta.warnings.map(escapeHtml).join(" ｜ ")}</p>` : ""}
<div class="wrap">
  <table>
    <thead><tr>${head}</tr></thead>
    <tbody>${body}</tbody>
  </table>
</div>
<footer>
  ${fmt(meta.rowsIn)} rows in · ${fmt(meta.cellsChanged)} cells changed · showing first ${Math.min(500, dataset.rows.length)} rows
</footer>
</body>
</html>`;
}
