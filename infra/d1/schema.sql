-- FlowTable · D1 schema
-- 跑法：pnpm db:migrate（本地） / pnpm db:migrate:prod（生产）
-- 原则：只存“规则与元数据”，不存客户的原始数据；快照放 R2，7 天过期。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workspaces (
  id          TEXT PRIMARY KEY,
  email       TEXT NOT NULL UNIQUE,
  api_key     TEXT NOT NULL UNIQUE,          -- TODO: 上线前改成 SHA-256 哈希存储
  plan        TEXT NOT NULL DEFAULT 'free',  -- free | starter | pro | team
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pipelines (
  id            TEXT PRIMARY KEY,
  workspace_id  TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  source        TEXT NOT NULL,                       -- JSON: { type: 'rest' | 'csv' | 'shopify' | 'stripe', ... }
  rules         TEXT NOT NULL,                       -- JSON: Rule[]
  schedule      TEXT NOT NULL DEFAULT 'daily',       -- daily | hourly | manual
  enabled       INTEGER NOT NULL DEFAULT 1,
  public_token  TEXT NOT NULL UNIQUE,                -- 托管表页 /t/:token
  last_rows     INTEGER,                             -- 上一次成功运行的行数，用于异常检测
  last_run_at   TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pipelines_ws ON pipelines(workspace_id);
CREATE INDEX IF NOT EXISTS idx_pipelines_due ON pipelines(enabled, schedule);

CREATE TABLE IF NOT EXISTS runs (
  id            TEXT PRIMARY KEY,
  pipeline_id   TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  status        TEXT NOT NULL,                       -- success | suspicious | failed
  rows_in       INTEGER,
  rows_out      INTEGER,
  cells_changed INTEGER,
  warnings      TEXT,                                -- JSON string[]
  error         TEXT,
  started_at    TEXT NOT NULL,
  finished_at   TEXT,
  duration_ms   INTEGER
);

CREATE INDEX IF NOT EXISTS idx_runs_pipeline ON runs(pipeline_id, started_at DESC);

CREATE TABLE IF NOT EXISTS subscriptions (
  workspace_id        TEXT PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
  provider            TEXT NOT NULL DEFAULT 'creem',
  customer_id         TEXT,
  subscription_id     TEXT,
  status              TEXT NOT NULL,                 -- active | past_due | canceled
  price_id            TEXT,
  current_period_end  TEXT,
  updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 轻量埋点：只记事件名与必要属性，用来算激活率与转化
CREATE TABLE IF NOT EXISTS events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id TEXT,
  name        TEXT NOT NULL,
  props       TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_events_name ON events(name, created_at DESC);
