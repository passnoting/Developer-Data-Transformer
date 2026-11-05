import { tableFromJson } from "@flowtable/core";
import type { Dataset } from "@flowtable/core";
import type { SourceConfig } from "../types.ts";

/**
 * 拉一个 REST/JSON 接口并转成表。
 *
 * 只做三件事，但都是“脏活”：
 * 1. 鉴权头（Bearer / 自定义 header）
 * 2. 分页（把 pageParam 从 1 递增，最多 pages 页）
 * 3. 选根 + 铺平（tableFromJson）
 */
export async function fetchRest(source: SourceConfig): Promise<Dataset> {
  if (!source.url) throw new Error("source.url 为空");

  const pages = Math.max(1, Math.min(source.pages ?? 1, 20)); // 上限保护：别把 Worker 打挂
  const pageParam = source.pageParam;
  const all: Dataset = { columns: [], rows: [] };

  for (let page = 1; page <= pages; page++) {
    const url = new URL(source.url);
    if (pageParam && pages > 1) url.searchParams.set(pageParam, String(page));

    const res = await fetch(url.toString(), {
      method: source.method ?? "GET",
      headers: {
        accept: "application/json",
        "user-agent": "FlowTable/0.1 (+https://flowtable.dev)",
        ...(source.headers ?? {}),
      },
      // 给上游一个明确的超时信号，别让一次抓取拖死整个 cron
      signal: AbortSignal.timeout(15_000),
    });

    if (!res.ok) {
      throw new Error(`上游返回 ${res.status} ${res.statusText}（${url.pathname}）`);
    }

    const payload = await res.json();
    const part = tableFromJson(payload, source.root);

    for (const c of part.columns) if (!all.columns.includes(c)) all.columns.push(c);
    all.rows.push(...part.rows);

    // 少于预期说明没有下一页了，提前收工
    if (part.rows.length === 0) break;
  }

  // 列并集补齐
  for (const row of all.rows) {
    for (const c of all.columns) if (row[c] === undefined) row[c] = null;
  }
  return all;
}
