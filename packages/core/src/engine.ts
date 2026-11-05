import { RULES } from "./rules.ts";
import type { CellDiff, Dataset, Row, Rule, RunResult } from "./types.ts";

export interface RunOptions {
  /** 最多记录多少条逐格 diff（界面只显示前 N 条，避免大文件卡死） */
  maxDiffs?: number;
}

/**
 * 执行一条清洗管道。
 *
 * 设计约束：
 * - 纯函数式：不修改入参（内部深拷贝一层）。
 * - 可追溯：每个改动的格子都记进 diffs，并指回**输入数据**的原始行号。
 * - 可解释：所有“没改动但需要注意”的情况（歧义日期、必填为空）进 warnings。
 */
export function runPipeline(
  input: Dataset,
  rules: Rule[],
  options: RunOptions = {},
): RunResult {
  const maxDiffs = options.maxDiffs ?? 500;
  const warnings = new Set<string>();
  const diffs: CellDiff[] = [];
  let changed = 0;
  let truncated = false;

  const ds: Dataset = {
    columns: [...input.columns],
    rows: input.rows.map((r) => ({ ...r })),
  };

  const rowIndex = new WeakMap<Row, number>();
  ds.rows.forEach((r, i) => rowIndex.set(r, i + 1));

  const recordDiff = (
    row: Row,
    column: string,
    before: unknown,
    after: unknown,
    ruleId: string,
  ): void => {
    changed += 1;
    if (diffs.length >= maxDiffs) {
      truncated = true;
      return;
    }
    diffs.push({
      row: rowIndex.get(row) ?? -1,
      column,
      before: before as CellDiff["before"],
      after: after as CellDiff["after"],
      rule: ruleId,
    });
  };

  const ctx = {
    diffs,
    warnings,
    maxDiffs,
    rowIndex,
    recordDiff,
    warn: (message: string) => warnings.add(message),
  };
  let applied = 0;
  for (const rule of rules) {
    const fn = RULES[rule.type as keyof typeof RULES];
    if (!fn) {
      warnings.add(`未知规则类型：${rule.type}（已跳过）`);
      continue;
    }
    fn(ds, rule, ctx);
    applied += 1;
  }

  const droppedColumns = input.columns.filter((c) => !ds.columns.includes(c));

  return {
    dataset: ds,
    diffs,
    warnings: [...warnings],
    diffsTruncated: truncated,
    stats: {
      rowsIn: input.rows.length,
      rowsOut: ds.rows.length,
      droppedRows: input.rows.length - ds.rows.length,
      droppedColumns,
      cellsChanged: changed,
      rulesApplied: applied,
    },
  };
}

/**
 * 判断一次运行是否“看起来不对”——定时任务里用它决定要不要发告警。
 * 规则很简单：行数相对上一次波动超过阈值，或者直接归零。
 */
export function isSuspicious(
  rowsOut: number,
  previousRows: number | null,
  tolerance = 0.2,
): boolean {
  if (rowsOut === 0) return true;
  if (previousRows === null || previousRows <= 0) return false;
  const delta = Math.abs(rowsOut - previousRows) / previousRows;
  return delta > tolerance;
}
