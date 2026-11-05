import type { D1Database, PipelineRow, WorkspaceRow } from "./types.ts";

export async function workspaceByApiKey(
  db: D1Database,
  apiKey: string,
): Promise<WorkspaceRow | null> {
  // TODO(上线前)：api_key 改成 SHA-256 哈希后比对，避免拖库即泄露
  return db
    .prepare("SELECT id, email, api_key, plan FROM workspaces WHERE api_key = ?")
    .bind(apiKey)
    .first<WorkspaceRow>();
}

export async function listPipelines(  db: D1Database,
  workspaceId: string,
): Promise<PipelineRow[]> {
  const res = await db
    .prepare(
      "SELECT * FROM pipelines WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 100",
    )
    .bind(workspaceId)
    .all<PipelineRow>();
  return res.results;
}

export async function getPipeline(db: D1Database, id: string): Promise<PipelineRow | null> {
  return db.prepare("SELECT * FROM pipelines WHERE id = ?").bind(id).first<PipelineRow>();
}

export async function pipelineByToken(
  db: D1Database,
  token: string,
): Promise<PipelineRow | null> {
  return db
    .prepare("SELECT * FROM pipelines WHERE public_token = ?")
    .bind(token)
    .first<PipelineRow>();
}

export async function createPipeline(
  db: D1Database,
  row: {
    id: string;
    workspaceId: string;
    name: string;
    source: string;
    rules: string;
    schedule: string;
    publicToken: string;
  },
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO pipelines (id, workspace_id, name, source, rules, schedule, public_token)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
    )
    .bind(
      row.id,
      row.workspaceId,
      row.name,
      row.source,
      row.rules,
      row.schedule,
      row.publicToken,
    )
    .run();
}

export async function startRun(
  db: D1Database,
  row: { id: string; pipelineId: string; startedAt: string },
): Promise<void> {
  await db
    .prepare(
      "INSERT INTO runs (id, pipeline_id, status, started_at) VALUES (?, ?, 'failed', ?)",
    )
    .bind(row.id, row.pipelineId, row.startedAt)
    .run();
}

/** 运行时把结果写回同一条 run 记录；status 由 runner 判定 */
export async function finishRun(
  db: D1Database,
  row: {
    id: string;
    status: "success" | "suspicious" | "failed";
    rowsIn: number | null;
    rowsOut: number | null;
    cellsChanged: number | null;
    warnings: string[];
    error: string | null;
    finishedAt: string;
    durationMs: number;
  },
): Promise<void> {
  await db
    .prepare(
      `UPDATE runs
          SET status = ?, rows_in = ?, rows_out = ?, cells_changed = ?,
              warnings = ?, error = ?, finished_at = ?, duration_ms = ?
        WHERE id = ?`,
    )
    .bind(
      row.status,
      row.rowsIn,
      row.rowsOut,
      row.cellsChanged,
      JSON.stringify(row.warnings),
      row.error,
      row.finishedAt,
      row.durationMs,
      row.id,
    )
    .run();
}

export async function touchPipeline(
  db: D1Database,
  id: string,
  rowsOut: number,
  at: string,
): Promise<void> {
  await db
    .prepare("UPDATE pipelines SET last_rows = ?, last_run_at = ? WHERE id = ?")
    .bind(rowsOut, at, id)
    .run();
}

/** 告警收件人：暂时就是注册邮箱；以后 pipelines.alert_email 优先 */
export async function workspaceEmailById(
  db: D1Database,
  workspaceId: string,
): Promise<string | null> {
  const row = await db
    .prepare("SELECT email FROM workspaces WHERE id = ?")
    .bind(workspaceId)
    .first<{ email: string }>();
  return row?.email ?? null;
}

export async function upsertSubscription(
  db: D1Database,
  row: {
    workspaceId: string;
    customerId: string | null;
    subscriptionId: string | null;
    status: string;
    priceId: string | null;
    currentPeriodEnd: string | null;
  },
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO subscriptions (workspace_id, customer_id, subscription_id, status, price_id, current_period_end, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(workspace_id) DO UPDATE SET
         customer_id = excluded.customer_id,
         subscription_id = excluded.subscription_id,
         status = excluded.status,
         price_id = excluded.price_id,
         current_period_end = excluded.current_period_end,
         updated_at = datetime('now')`,
    )
    .bind(
      row.workspaceId,
      row.customerId,
      row.subscriptionId,
      row.status,
      row.priceId,
      row.currentPeriodEnd,
    )
    .run();
}

/** 订阅状态决定能建几条管道；这是唯一的“付费墙”实现点 */
export async function pipelineLimit(db: D1Database, workspaceId: string): Promise<number> {
  const sub = await db
    .prepare("SELECT status, price_id FROM subscriptions WHERE workspace_id = ?")
    .bind(workspaceId)
    .first<{ status: string; price_id: string | null }>();

  if (!sub || sub.status !== "active") return 1; // 免费：1 条，只能手动跑
  const price = sub.price_id ?? "";
  if (price.includes("pro")) return 20;
  if (price.includes("team")) return 100;
  return 3; // starter
}
