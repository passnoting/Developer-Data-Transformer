/**
 * 最小化的 Cloudflare 绑定类型声明。
 * 故意不依赖 @cloudflare/workers-types —— 让脚手架 `pnpm install` 之前也能读、能改。
 * 真正 ship 时可以换成官方类型，字段是结构兼容的。
 */

export interface D1Result<T> {
  results: T[];
  success: boolean;
}

export interface D1PreparedStatement {
  bind(...values: unknown[]): D1PreparedStatement;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  all<T = Record<string, unknown>>(): Promise<D1Result<T>>;
  run(): Promise<unknown>;
}

export interface D1Database {
  prepare(query: string): D1PreparedStatement;
  batch(statements: D1PreparedStatement[]): Promise<unknown>;
}

export interface R2ObjectBody {
  text(): Promise<string>;
}

export interface R2Bucket {
  put(key: string, value: string | ArrayBuffer | Uint8Array): Promise<unknown>;
  get(key: string): Promise<R2ObjectBody | null>;
  delete(key: string): Promise<void>;
}

export interface Env {
  DB: D1Database;
  SNAPSHOTS: R2Bucket;
  APP_URL: string;
  ALERT_FROM: string;
  CREEM_WEBHOOK_SECRET?: string;
  RESEND_API_KEY?: string;
}

export interface PipelineRow {
  id: string;
  workspace_id: string;
  name: string;
  source: string;
  rules: string;
  schedule: string;
  enabled: number;
  public_token: string;
  last_rows: number | null;
  last_run_at: string | null;
}

export interface WorkspaceRow {
  id: string;
  email: string;
  api_key: string;
  plan: string;
}

export interface SourceConfig {
  type: "rest" | "csv" | "shopify" | "stripe";
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  /** JSONPath 风格的取值路径，如 data.items */
  root?: string;
  /** 分页：把 pageParam 从 1 递增到 pages */
  pages?: number;
  pageParam?: string;
  /** 直接给一段 CSV（手工粘贴/小文件场景） */
  csv?: string;
}

export interface SnapshotMeta {
  pipelineId: string;
  name: string;
  updatedAt: string;
  rowsOut: number;
  rowsIn: number;
  cellsChanged: number;
  warnings: string[];
}

/** Cloudflare 的 cron 事件（只用到 cron 表达式与时间） */
export interface ScheduledController {
  cron: string;
  scheduledTime: number;
}
