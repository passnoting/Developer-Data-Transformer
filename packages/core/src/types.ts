/** 数据模型：整个系统里流转的就是这三样东西 —— 表结构、行、规则。 */

export type CellValue = string | number | boolean | null;

/** 一行数据。键 = 列名。 */
export type Row = Record<string, CellValue>;

export interface Dataset {
  columns: string[];
  rows: Row[];
}

export type RuleType =
  | "trim"
  | "dropEmptyRows"
  | "dropEmptyColumns"
  | "normalizeDates"
  | "coerceNumbers"
  | "normalizeCase"
  | "dedupe"
  | "splitColumn"
  | "mergeColumns"
  | "mapEnum"
  | "requireFields"
  | "rangeCheck";

export interface Rule {
  /** 稳定 id，用于 diff 溯源与撤销 */
  id: string;
  type: RuleType;
  /** 大多数规则作用在单列上 */
  column?: string;
  options?: Record<string, unknown>;
}

/** 一个格子的改动记录。row 是「输入数据」里的 1-based 行号，删行也不会错位。 */
export interface CellDiff {
  row: number;
  column: string;
  before: CellValue;
  after: CellValue;
  rule: string;
}

export interface RunStats {
  rowsIn: number;
  rowsOut: number;
  droppedRows: number;
  droppedColumns: string[];
  cellsChanged: number;
  rulesApplied: number;
}

export interface RunResult {
  dataset: Dataset;
  diffs: CellDiff[];
  /** 每条规则产生的告警（如“检测到歧义日期”），去重后给用户看 */
  warnings: string[];
  stats: RunStats;
  /** diff 超过上限时被截断，界面上要提示“只显示前 N 条” */
  diffsTruncated: boolean;
}
