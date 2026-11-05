import type { CellValue, Dataset, Row, Rule } from "./types.ts";

/** 规则执行时的可变上下文，由 engine 传入。 */
export interface RuleContext {
  diffs: import("./types.ts").CellDiff[];
  warnings: Set<string>;
  maxDiffs: number;
  /** 行 → 输入数据里的 1-based 行号 */
  rowIndex: WeakMap<Row, number>;
  recordDiff: (row: Row, column: string, before: CellValue, after: CellValue, ruleId: string) => void;
  warn: (message: string) => void;
}

const EMPTY = (v: CellValue): boolean =>
  v === null || v === undefined || (typeof v === "string" && v.trim() === "");

const asString = (v: CellValue): string => (v === null || v === undefined ? "" : String(v));

function setCell(
  row: Row,
  column: string,
  next: CellValue,
  rule: Rule,
  ctx: RuleContext,
): void {
  const before = row[column] ?? null;
  if (before === next) return;
  row[column] = next;
  ctx.recordDiff(row, column, before, next, rule.id);
}

/* ------------------------------------------------------------------ */
/* 1. trim：去首尾空白 + 折叠中间连续空格                                */
/* ------------------------------------------------------------------ */
export function trim(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  for (const row of ds.rows) {
    const v = row[col];
    if (typeof v !== "string") continue;
    const next = v.replace(/\s+/g, " ").trim();
    setCell(row, col, next, rule, ctx);
  }
  return ds;
}

/* ------------------------------------------------------------------ */
/* 2. dropEmptyRows                                                   */
/* ------------------------------------------------------------------ */
export function dropEmptyRows(ds: Dataset, _rule: Rule, ctx: RuleContext): Dataset {
  const before = ds.rows.length;
  ds.rows = ds.rows.filter((row) => ds.columns.some((c) => !EMPTY(row[c] ?? null)));
  const dropped = before - ds.rows.length;
  if (dropped > 0) ctx.warn(`删除空行 ${dropped} 行`);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 3. dropEmptyColumns                                                */
/* ------------------------------------------------------------------ */
export function dropEmptyColumns(ds: Dataset, _rule: Rule, ctx: RuleContext): Dataset {
  const keep = ds.columns.filter((c) => ds.rows.some((row) => !EMPTY(row[c] ?? null)));
  const dropped = ds.columns.filter((c) => !keep.includes(c));
  if (dropped.length > 0) ctx.warn(`删除空列 ${dropped.length} 列：${dropped.join("、")}`);
  for (const row of ds.rows) for (const c of dropped) delete row[c];
  ds.columns = keep;
  return ds;
}

/* ------------------------------------------------------------------ */
/* 4. normalizeDates：统一成 ISO（YYYY-MM-DD），有歧义就告警             */
/* ------------------------------------------------------------------ */
const ISO_DATE = /^(\d{4})-(\d{1,2})-(\d{1,2})/;
const YMD_SLASH = /^(\d{4})\/(\d{1,2})\/(\d{1,2})$/;
const MDY_SLASH = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
const DMY_DOT = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/;

const pad = (n: number): string => String(n).padStart(2, "0");

export function normalizeDates(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  let ambiguous = 0;

  for (const row of ds.rows) {
    const raw = row[col];
    if (typeof raw !== "string" || raw.trim() === "") continue;
    const s = raw.trim();

    let iso: string | null = null;
    let m: RegExpMatchArray | null;

    if ((m = s.match(ISO_DATE))) {
      iso = `${m[1]}-${pad(+m[2])}-${pad(+m[3])}`;
    } else if ((m = s.match(YMD_SLASH))) {
      iso = `${m[1]}-${pad(+m[2])}-${pad(+m[3])}`;
    } else if ((m = s.match(DMY_DOT))) {
      iso = `${m[3]}-${pad(+m[2])}-${pad(+m[1])}`;
    } else if ((m = s.match(MDY_SLASH))) {
      const a = +m[1];
      const b = +m[2];
      if (a <= 12 && b <= 12) ambiguous += 1;
      iso = `${m[3]}-${pad(a)}-${pad(b)}`;
    } else {
      const t = Date.parse(s);
      if (!Number.isNaN(t)) iso = new Date(t).toISOString().slice(0, 10);
    }

    if (iso && iso !== s) setCell(row, col, iso, rule, ctx);
  }

  if (ambiguous > 0) {
    ctx.warn(`${ambiguous} 个日期形如 MM/DD 与 DD/MM 无法区分，已按美式 MM/DD 解析`);
  }
  return ds;
}

/* ------------------------------------------------------------------ */
/* 5. coerceNumbers：$1,234.50 / (1,234) / 12% → 数字                    */
/* ------------------------------------------------------------------ */
export function coerceNumbers(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  let failed = 0;

  for (const row of ds.rows) {
    const raw = row[col];
    if (typeof raw === "number" || typeof raw === "boolean") continue;
    if (raw === null || raw === undefined) continue;
    const s = String(raw).trim();
    if (s === "") continue;

    let body = s.replace(/[$€£¥,\s]/g, "");
    let sign = 1;
    if (/^\(.*\)$/.test(body)) {
      sign = -1;
      body = body.slice(1, -1);
    }
    body = body.replace(/%$/, "");
    if (!/^-?\d+(\.\d+)?$/.test(body)) {
      failed += 1;
      continue;
    }
    const n = sign * Number(body);
    if (n !== raw) setCell(row, col, n, rule, ctx);
  }

  if (failed > 0) ctx.warn(`「${col}」有 ${failed} 个值无法转成数字，已保留原样`);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 6. normalizeCase：lower / upper / title                             */
/* ------------------------------------------------------------------ */
export function normalizeCase(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  const mode = String(rule.options?.case ?? "lower");
  for (const row of ds.rows) {
    const v = row[col];
    if (typeof v !== "string") continue;
    const next =
      mode === "upper"
        ? v.toUpperCase()
        : mode === "title"
          ? v.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase())
          : v.toLowerCase();
    setCell(row, col, next, rule, ctx);
  }
  return ds;
}

/* ------------------------------------------------------------------ */
/* 7. dedupe：按指定列（默认全部列）去重，保留第一条                     */
/* ------------------------------------------------------------------ */
export function dedupe(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const keys = (rule.options?.keys as string[] | undefined) ?? ds.columns;
  const caseInsensitive = rule.options?.caseInsensitive !== false;
  const seen = new Set<string>();
  const before = ds.rows.length;

  ds.rows = ds.rows.filter((row) => {
    const k = keys
      .map((c) => {
        const v = asString(row[c] ?? null).trim();
        return caseInsensitive ? v.toLowerCase() : v;
      })
      .join("\u0001");
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  const dropped = before - ds.rows.length;
  if (dropped > 0) ctx.warn(`按「${keys.join(" + ")}」删除重复行 ${dropped} 行（保留第一条）`);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 8. splitColumn：按分隔符拆成多列                                     */
/* ------------------------------------------------------------------ */
export function splitColumn(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  const delimiter = String(rule.options?.delimiter ?? ",");
  const into = (rule.options?.into as string[] | undefined) ?? [`${col}_1`, `${col}_2`];

  for (const row of ds.rows) {
    const v = row[col];
    if (v === null || v === undefined) continue;
    const parts = String(v).split(delimiter).map((p) => p.trim());
    into.forEach((name, i) => {
      row[name] = parts[i] ?? null;
    });
  }

  const at = ds.columns.indexOf(col);
  const fresh = into.filter((c) => !ds.columns.includes(c));
  ds.columns.splice(at + 1, 0, ...fresh);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 9. mergeColumns：多列合并成一列                                      */
/* ------------------------------------------------------------------ */
export function mergeColumns(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const cols = (rule.options?.columns as string[] | undefined) ?? (rule.column ? [rule.column] : []);
  if (cols.length === 0) return ds;
  const into = String(rule.options?.into ?? cols.join("_"));
  const sep = String(rule.options?.separator ?? " ");

  for (const row of ds.rows) {
    const joined = cols
      .map((c) => asString(row[c] ?? null).trim())
      .filter((s) => s !== "")
      .join(sep);
    row[into] = joined === "" ? null : joined;
  }
  if (!ds.columns.includes(into)) ds.columns.push(into);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 10. mapEnum：把同义词映射成统一值（状态、国家、渠道名最常见）          */
/* ------------------------------------------------------------------ */
export function mapEnum(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  const mapping = (rule.options?.mapping as Record<string, string> | undefined) ?? {};
  const ci = rule.options?.caseInsensitive !== false;
  const table = new Map<string, string>();
  for (const [k, v] of Object.entries(mapping)) table.set(ci ? k.toLowerCase() : k, v);

  let hit = 0;
  for (const row of ds.rows) {
    const v = row[col];
    if (v === null || v === undefined) continue;
    const key = ci ? String(v).trim().toLowerCase() : String(v).trim();
    const mapped = table.get(key);
    if (mapped !== undefined && mapped !== v) {
      setCell(row, col, mapped, rule, ctx);
      hit += 1;
    }
  }
  if (hit === 0) ctx.warn(`「${col}」没有命中任何映射规则，检查大小写或映射表`);
  return ds;
}

/* ------------------------------------------------------------------ */
/* 11. requireFields：只告警，不删行（删了会丢数据，由用户决定）           */
/* ------------------------------------------------------------------ */
export function requireFields(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const cols = (rule.options?.columns as string[] | undefined) ?? (rule.column ? [rule.column] : []);
  for (const col of cols) {
    const bad = ds.rows.filter((r) => EMPTY(r[col] ?? null)).length;
    if (bad > 0) ctx.warn(`「${col}」有 ${bad} 行必填为空`);
  }
  return ds;
}

/* ------------------------------------------------------------------ */
/* 12. rangeCheck：数值越界告警（用于抓“多打一个零”）                    */
/* ------------------------------------------------------------------ */
export function rangeCheck(ds: Dataset, rule: Rule, ctx: RuleContext): Dataset {
  const col = rule.column;
  if (!col) return ds;
  const min = rule.options?.min !== undefined ? Number(rule.options.min) : -Infinity;
  const max = rule.options?.max !== undefined ? Number(rule.options.max) : Infinity;
  let bad = 0;
  for (const row of ds.rows) {
    const v = row[col];
    if (typeof v !== "number") continue;
    if (v < min || v > max) bad += 1;
  }
  if (bad > 0) ctx.warn(`「${col}」有 ${bad} 个值超出 [${min}, ${max}] 区间`);
  return ds;
}

export const RULES = {
  trim,
  dropEmptyRows,
  dropEmptyColumns,
  normalizeDates,
  coerceNumbers,
  normalizeCase,
  dedupe,
  splitColumn,
  mergeColumns,
  mapEnum,
  requireFields,
  rangeCheck,
} as const;
