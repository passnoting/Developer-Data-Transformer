import { toCsv } from "@flowtable/core";
import type { Dataset } from "@flowtable/core";
import { verifySignature, mapEventToStatus, workspaceIdFromEvent } from "./billing.ts";
import type { CreemEvent } from "./billing.ts";
import {
  createPipeline,
  getPipeline,
  listPipelines,
  pipelineByToken,
  pipelineLimit,
  upsertSubscription,
  workspaceByApiKey,
} from "./db.ts";
import { renderHostedPage } from "./hosted.ts";
import { executePipeline } from "./runner.ts";
import type { Env, PipelineRow, ScheduledController, SnapshotMeta } from "./types.ts";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "access-control-allow-headers": "authorization,content-type",
};

const json = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { ...JSON_HEADERS, ...CORS } });

const fail = (message: string, status = 400): Response => json({ error: message }, status);

const bearer = (req: Request): string | null => {
  const h = req.headers.get("authorization") ?? "";
  return h.toLowerCase().startsWith("bearer ") ? h.slice(7).trim() : null;
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;

    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });

    try {
      /* ---------------- 公开路由 ---------------- */

      if (path === "/api/health") {
        return json({ ok: true, version: "0.1.0", now: new Date().toISOString() });
      }

      // 托管表页（公开，靠不可猜的 token 保护；后续可加密码/域名白名单）
      const page = path.match(/^\/t\/([A-Za-z0-9_-]{16,})$/);
      if (page && req.method === "GET") {
        const pipeline = await pipelineByToken(env.DB, page[1]);
        if (!pipeline) return new Response("Not found", { status: 404 });
        const snapshot = await env.SNAPSHOTS.get(`snapshots/${pipeline.public_token}.json`);
        if (!snapshot) return new Response("This table has not run yet.", { status: 404 });
        const { meta, dataset } = JSON.parse(await snapshot.text()) as {
          meta: SnapshotMeta;
          dataset: Dataset;
        };
        return new Response(renderHostedPage(meta, dataset, `/t/${pipeline.public_token}.csv`), {
          headers: { "content-type": "text/html; charset=utf-8" },
        });
      }

      const csvRoute = path.match(/^\/t\/([A-Za-z0-9_-]{16,})\.csv$/);
      if (csvRoute && req.method === "GET") {
        const pipeline = await pipelineByToken(env.DB, csvRoute[1]);
        if (!pipeline) return new Response("Not found", { status: 404 });
        const snapshot = await env.SNAPSHOTS.get(`snapshots/${pipeline.public_token}.json`);
        if (!snapshot) return new Response("This table has not run yet.", { status: 404 });
        const { dataset } = JSON.parse(await snapshot.text()) as { dataset: Dataset };
        return new Response(toCsv(dataset), {
          headers: {
            "content-type": "text/csv; charset=utf-8",
            "content-disposition": `attachment; filename="${pipeline.name.replace(/[^\w-]+/g, "-")}.csv"`,
          },
        });
      }

      // 计费回调（靠签名，不靠 API key）
      if (path === "/api/webhooks/creem" && req.method === "POST") {
        const raw = await req.text();
        const ok = await verifySignature(
          raw,
          req.headers.get("creem-signature"),
          env.CREEM_WEBHOOK_SECRET,
        );
        if (!ok) return fail("invalid signature", 401);

        const event = JSON.parse(raw) as CreemEvent;
        const mapped = mapEventToStatus(event.type);
        const workspaceId = workspaceIdFromEvent(event);
        if (mapped && workspaceId) {
          await upsertSubscription(env.DB, {
            workspaceId,
            customerId: event.data?.customer?.id ?? null,
            subscriptionId: event.data?.subscription?.id ?? null,
            status: mapped.status,
            priceId: event.data?.subscription?.product_id ?? null,
            currentPeriodEnd: event.data?.current_period_end ?? null,
          });
        }
        return json({ received: true, handled: Boolean(mapped) });
      }

      /* ---------------- 需要 API key 的路由 ---------------- */

      if (path.startsWith("/api/pipelines")) {
        const key = bearer(req);
        if (!key) return fail("missing bearer token", 401);
        const workspace = await workspaceByApiKey(env.DB, key);
        if (!workspace) return fail("invalid api key", 401);

        // GET /api/pipelines
        if (path === "/api/pipelines" && req.method === "GET") {
          const rows = await listPipelines(env.DB, workspace.id);
          return json({
            pipelines: rows.map((p) => ({
              id: p.id,
              name: p.name,
              schedule: p.schedule,
              enabled: Boolean(p.enabled),
              rows: p.last_rows,
              lastRunAt: p.last_run_at,
              tableUrl: `${env.APP_URL}/t/${p.public_token}`,
            })),
          });
        }

        // POST /api/pipelines
        if (path === "/api/pipelines" && req.method === "POST") {
          const body = (await req.json()) as Partial<{
            name: string;
            source: unknown;
            rules: unknown;
            schedule: string;
          }>;
          if (!body.name || !body.source || !body.rules) {
            return fail("name / source / rules 均为必填");
          }

          const existing = await listPipelines(env.DB, workspace.id);
          const limit = await pipelineLimit(env.DB, workspace.id);
          if (existing.length >= limit) {
            return fail(`当前套餐最多 ${limit} 条管道，请升级`, 402);
          }

          const id = crypto.randomUUID();
          const publicToken = crypto.randomUUID().replace(/-/g, "");
          await createPipeline(env.DB, {
            id,
            workspaceId: workspace.id,
            name: body.name,
            source: JSON.stringify(body.source),
            rules: JSON.stringify(body.rules),
            schedule: body.schedule === "hourly" ? "hourly" : "daily",
            publicToken,
          });
          return json({ id, tableUrl: `${env.APP_URL}/t/${publicToken}` }, 201);
        }

        // POST /api/pipelines/:id/run
        const runMatch = path.match(/^\/api\/pipelines\/([\w-]+)\/run$/);
        if (runMatch && req.method === "POST") {
          const pipeline = await getPipeline(env.DB, runMatch[1]);
          if (!pipeline || pipeline.workspace_id !== workspace.id) {
            return fail("pipeline not found", 404);
          }
          const summary = await executePipeline(env, pipeline, "manual");
          return json(summary, summary.status === "failed" ? 502 : 200);
        }

        return fail("not found", 404);
      }

      return fail("not found", 404);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error("[api] unhandled", message);
      return fail(`internal error: ${message}`, 500);
    }
  },

  /**
   * 定时任务。
   * v0.1 串行跑，先保证“小客户也能跑完”；管道数上千后换 Cloudflare Queues，
   * 否则单次 cron 会撞 CPU 上限（这里也是最容易埋雷的地方）。
   */
  async scheduled(event: ScheduledController, env: Env): Promise<void> {
    const hourly = event.cron === "0 * * * *";
    const rows = await env.DB.prepare(
      hourly
        ? "SELECT * FROM pipelines WHERE enabled = 1 AND schedule = 'hourly'"
        : "SELECT * FROM pipelines WHERE enabled = 1",
    ).all<PipelineRow>();

    for (const pipeline of rows.results) {
      try {
        await executePipeline(env, pipeline, "cron");
      } catch (err) {
        console.error(`[cron] pipeline ${pipeline.id} failed`, err);
      }
    }
  },
};
