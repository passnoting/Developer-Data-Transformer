import { isSuspicious, parseCsv, runPipeline } from "@flowtable/core";
import type { Dataset, Rule } from "@flowtable/core";
import { sendAlert } from "./alerts.ts";
import { fetchRest } from "./connectors/rest.ts";
import { finishRun, startRun, touchPipeline, workspaceEmailById } from "./db.ts";
import type { Env, PipelineRow, SnapshotMeta, SourceConfig } from "./types.ts";

/** 单次快照最多存多少行；超出的部分丢弃并告警（保护 R2 与页面渲染） */
const MAX_SNAPSHOT_ROWS = 20_000;

export interface RunSummary {
  runId: string;
  status: "success" | "suspicious" | "failed";
  rowsIn: number;
  rowsOut: number;
  cellsChanged: number;
  warnings: string[];
  error?: string;
  durationMs: number;
}

export async function loadSource(source: SourceConfig): Promise<Dataset> {
  switch (source.type) {
    case "rest":
    case "shopify":
    case "stripe":
      // v0.1：shopify / stripe 只是“预填好 URL 与鉴权头”的 rest，真正的差异在 web 端的表单
      return fetchRest(source);
    case "csv":
      if (!source.csv) throw new Error("source.csv 为空");
      return parseCsv(source.csv);
    default:
      throw new Error(`不支持的数据源类型：${(source as { type?: string }).type}`);
  }
}

export async function executePipeline(
  env: Env,
  pipeline: PipelineRow,
  trigger: "cron" | "manual",
): Promise<RunSummary> {
  const runId = crypto.randomUUID();
  const startedAt = new Date().toISOString();
  const t0 = Date.now();
  const alertTo = await workspaceEmailById(env.DB, pipeline.workspace_id);
  await startRun(env.DB, { id: runId, pipelineId: pipeline.id, startedAt });

  try {
    const source = JSON.parse(pipeline.source) as SourceConfig;
    const rules = JSON.parse(pipeline.rules) as Rule[];

    const input = await loadSource(source);
    const result = runPipeline(input, rules, { maxDiffs: 200 });

    const warnings = [...result.warnings];
    let out = result.dataset;
    if (out.rows.length > MAX_SNAPSHOT_ROWS) {
      warnings.push(`结果超过 ${MAX_SNAPSHOT_ROWS} 行，快照只保留前 ${MAX_SNAPSHOT_ROWS} 行`);
      out = { columns: out.columns, rows: out.rows.slice(0, MAX_SNAPSHOT_ROWS) };
    }

    const meta: SnapshotMeta = {
      pipelineId: pipeline.id,
      name: pipeline.name,
      updatedAt: new Date().toISOString(),
      rowsIn: result.stats.rowsIn,
      rowsOut: result.stats.rowsOut,
      cellsChanged: result.stats.cellsChanged,
      warnings,
    };
    await env.SNAPSHOTS.put(
      `snapshots/${pipeline.public_token}.json`,
      JSON.stringify({ meta, dataset: out }),
    );

    // 关键判断：行数异常 = 要么上游挂了，要么规则把数据吃掉了，两种都该喊人
    const suspicious = isSuspicious(result.stats.rowsOut, pipeline.last_rows);
    const status = suspicious ? "suspicious" : "success";
    const finishedAt = new Date().toISOString();
    const durationMs = Date.now() - t0;

    await finishRun(env.DB, {
      id: runId,
      status,
      rowsIn: result.stats.rowsIn,
      rowsOut: result.stats.rowsOut,
      cellsChanged: result.stats.cellsChanged,
      warnings,
      error: null,
      finishedAt,
      durationMs,
    });
    await touchPipeline(env.DB, pipeline.id, result.stats.rowsOut, finishedAt);

    if (suspicious) {
      await sendAlert(env, alertTo, {
        subject: `「${pipeline.name}」行数异常：${pipeline.last_rows ?? "?"} → ${result.stats.rowsOut}`,
        body: [
          `管道：${pipeline.name}`,
          `上次行数：${pipeline.last_rows ?? "首次运行"}`,
          `本次行数：${result.stats.rowsOut}`,
          `时间：${finishedAt}`,
          `查看：${env.APP_URL}/t/${pipeline.public_token}`,
        ].join("\n"),
      });
    }

    return {
      runId,
      status,
      rowsIn: result.stats.rowsIn,
      rowsOut: result.stats.rowsOut,
      cellsChanged: result.stats.cellsChanged,
      warnings,
      durationMs,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    const finishedAt = new Date().toISOString();
    await finishRun(env.DB, {
      id: runId,
      status: "failed",
      rowsIn: null,
      rowsOut: null,
      cellsChanged: null,
      warnings: [],
      error: message,
      finishedAt,
      durationMs: Date.now() - t0,
    });
    await sendAlert(env, alertTo, {
      subject: `「${pipeline.name}」运行失败`,
      body: `错误：${message}\n时间：${finishedAt}\n触发：${trigger}`,
    });
    return {
      runId,
      status: "failed",
      rowsIn: 0,
      rowsOut: 0,
      cellsChanged: 0,
      warnings: [],
      error: message,
      durationMs: Date.now() - t0,
    };
  }
}
