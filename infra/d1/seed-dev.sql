-- 本地开发用的假数据。只在 --local 的库上跑，不要在生产执行。
--   pnpm db:seed
-- 建出来的 workspace：
--   api_key = dev_key_123
--   套餐   = starter（3 条管道，因为同时插了一条 active 的订阅）

INSERT INTO workspaces (id, email, api_key, plan)
VALUES ('ws_demo', 'demo@example.com', 'dev_key_123', 'starter')
ON CONFLICT(id) DO NOTHING;

INSERT INTO subscriptions (workspace_id, provider, status, price_id)
VALUES ('ws_demo', 'creem', 'active', 'price_starter')
ON CONFLICT(workspace_id) DO NOTHING;
