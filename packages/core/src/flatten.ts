import type { CellValue, Dataset, Row } from "./types.ts";

export interface FlattenOptions {
  /** 嵌套分隔符，默认 "."（Google Sheets 里更常见的写法） */
  separator?: string;
  /** 最大展开深度，防止恶意/异常结构把内存打爆 */
  maxDepth?: number;
}

const isPlainObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

/**
 * 把嵌套对象压成一层。数组用 [i] 表示，例如 tags[0]。
 * 超过 maxDepth 的值直接 JSON.stringify，保留信息但不继续展开。
 */
export function flattenObject(
  input: Record<string, unknown>,
  options: FlattenOptions = {},
): Row {
  const sep = options.separator ?? ".";
  const maxDepth = options.maxDepth ?? 4;
  const out: Row = {};

  const walk = (value: unknown, path: string, depth: number): void => {
    if (path === "") return;

    if (value === null || value === undefined) {
      out[path] = null;
      return;
    }
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      out[path] = value as CellValue;
      return;
    }
    if (depth >= maxDepth) {
      out[path] = JSON.stringify(value);
      return;
    }
    if (Array.isArray(value)) {
      // 标量数组压成一个字符串，对象数组展开成 [i]
      const allScalar = value.every(
        (v) => v === null || ["string", "number", "boolean"].includes(typeof v),
      );
      if (allScalar) {
        out[path] = value.map((v) => (v === null ? "" : String(v))).join(",");
        return;
      }
      value.forEach((v, i) => walk(v, `${path}[${i}]`, depth + 1));
      return;
    }
    if (isPlainObject(value)) {
      for (const [k, v] of Object.entries(value)) {
        walk(v, path ? `${path}${sep}${k}` : k, depth + 1);
      }
      return;
    }
    out[path] = String(value);
  };

  for (const [k, v] of Object.entries(input)) walk(v, k, 0);
  return out;
}

/** 按 "data.items" 这样的路径取值，支持数组下标：data.items[0].rows */
export function pickPath(payload: unknown, path?: string): unknown {
  if (!path) return payload;
  let cur: unknown = payload;
  for (const raw of path.split(".")) {
    if (cur === null || cur === undefined) return undefined;
    const m = raw.match(/^(.+?)\[(\d+)\]$/);
    if (m) {
      cur = (cur as Record<string, unknown>)[m[1]];
      cur = Array.isArray(cur) ? cur[Number(m[2])] : undefined;
    } else {
      cur = (cur as Record<string, unknown>)[raw];
    }
  }
  return cur;
}

/**
 * 把任意 JSON 响应变成一张表。
 * - 数组 → 每项一行
 * - 对象里只有一个数组字段 → 用那个数组（API 最常见：{ data: [...] }）
 * - 单个对象 → 一行
 */
export function tableFromJson(payload: unknown, rootPath?: string): Dataset {
  const node = pickPath(payload, rootPath);

  let list: unknown[];
  if (Array.isArray(node)) {
    list = node;
  } else if (isPlainObject(node)) {
    const arrayFields = Object.entries(node).filter(([, v]) => Array.isArray(v));
    list = arrayFields.length === 1 ? (arrayFields[0][1] as unknown[]) : [node];
  } else if (node === null || node === undefined) {
    list = [];
  } else {
    list = [{ value: node }];
  }

  const rows: Row[] = list.map((item) =>
    isPlainObject(item) ? flattenObject(item) : { value: item as CellValue },
  );

  // 列取并集，保持首次出现顺序（不同行的字段可能不一样）
  const columns: string[] = [];
  const seen = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        columns.push(key);
      }
    }
  }

  for (const row of rows) {
    for (const c of columns) if (row[c] === undefined) row[c] = null;
  }

  return { columns, rows };
}
