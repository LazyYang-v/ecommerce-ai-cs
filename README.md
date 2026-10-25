# ecommerce-ai-cs · 电商智能客服 Agent 平台

Phase 1（工程基础）已交付：React 前端、FastAPI Business API、独立 FastAPI + LangGraph
Agent 服务、PostgreSQL 17、Redis 7 通过 Docker Compose 连通，并具备鉴权、迁移、测试与
真实浏览器联调的完整闭环。

## 架构总览

```
React Web (5173)  ──HTTP/SSE──▶  Business API (8000)  ──内部 HTTP──▶  Agent Service (8001)
                                      │        ▲                          │
                                      ▼        └──────── 受控工具调用 ─────┘ (Phase 2)
                                 PostgreSQL (55432)   Redis (56379)
```

两条铁律：

1. **前端只调用 Business API**，不直接访问 Agent 服务。
2. **Agent 不直接修改业务数据**，未来查询订单等一律经 Business API 的受控工具接口。

详见 [docs/architecture.md](docs/architecture.md)。

## 目录结构

```
apps/web      React + TypeScript + Vite 前端
apps/api      Business API（FastAPI + SQLAlchemy 2 + Alembic）
apps/agent    Agent 服务（FastAPI + LangGraph，Phase 1 为确定性测试响应）
packages/contracts  服务间 API 契约说明
infra/        预留（数据库扩展 SQL 等）
scripts/      smoke-test.sh 冒烟验收脚本
docs/         architecture / database / api-contracts
compose.yaml  本地编排（4 服务）
```

## 环境要求

- Docker Desktop 或 Docker Engine（含 Compose v2）
- [uv](https://docs.astral.sh/uv/) 0.12+（本地跑 Python 3.12 项目与迁移）
- Node.js 20+（前端开发）

## 快速开始

### 1. 环境变量

```bash
cp .env.example .env
# 为三个变量填入随机值，例如：
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
chmod 600 .env
```

### 2. 启动服务

```bash
docker compose up -d --build
docker compose ps          # postgres / redis / api / agent 均应 healthy
```

### 3. 数据库迁移（首次）

```bash
cd apps/api
DATABASE_URL="postgresql+asyncpg://ecommerce:<POSTGRES_PASSWORD>@127.0.0.1:55432/ecommerce" \
  uv run alembic upgrade head
```

### 4. 写入示例商品

```bash
DATABASE_URL="postgresql+asyncpg://ecommerce:<POSTGRES_PASSWORD>@127.0.0.1:55432/ecommerce" \
  uv run python scripts/seed_products.py
```

### 5. 前端

```bash
cd apps/web
npm install
npm run dev                # http://localhost:5173 （Vite 仅绑定 [::1]，用 localhost 访问）
```

### 6. 冒烟验收（28 项断言）

```bash
./scripts/smoke-test.sh
```

## 测试

```bash
# Business API（29 用例；DATABASE_URL 必须指向独立测试库 ecommerce_test，脚本会强制校验）
cd apps/api
DATABASE_URL="postgresql+asyncpg://ecommerce:<POSTGRES_PASSWORD>@127.0.0.1:55432/ecommerce_test" \
  uv run pytest -q
uv run ruff check .

# Agent 服务（9 用例）
cd apps/agent
uv run pytest -q && uv run ruff check .

# 前端
cd apps/web
npm run build && npm run lint
```

## 常用命令

```bash
docker compose logs -f api          # 跟踪日志（日志格式含 [request_id]）
docker compose exec postgres psql -U ecommerce -d ecommerce
docker compose restart api
docker compose stop                 # 停止全部容器（数据保留在 volume）
docker compose down                 # 移除容器（volume 默认保留；--volumes 会删数据，慎用）
```

## 端口（宿主机侧全部只绑定 127.0.0.1）

| 服务 | 宿主机端口 | 容器端口 |
|---|---|---|
| web（本机 dev） | 5173 | — |
| api | 8000 | 8000 |
| agent | 8001 | 8001（生产环境不应暴露） |
| postgres | 55432 | 5432 |
| redis | 56379 | 6379 |

## 环境变量

| 变量 | 用途 | 注入位置 |
|---|---|---|
| `POSTGRES_PASSWORD` | 数据库密码 | postgres / api（拼入 DATABASE_URL） |
| `INTERNAL_SERVICE_TOKEN` | Business API ↔ Agent 内部互信令牌 | api / agent |
| `JWT_SECRET` | 用户 JWT 签名密钥 | api |
| `DATABASE_URL` | 异步连接串（容器内由 compose 注入） | api |
| `REDIS_URL` | Redis 连接串（Phase 1 仅注入未使用） | api |
| `AGENT_URL` / `BUSINESS_API_URL` | 服务发现地址（容器网络） | api / agent |
| `AGENT_TIMEOUT_SECONDS` | API 调 Agent 超时（默认 15s） | api |

## 本机环境备注

- 本机 Docker 默认地址池已耗尽（历史项目网络众多），compose 为本项目固定子网
  `10.99.0.0/24`，不影响其他项目。
- 测试库 `ecommerce_test` 与开发库 `ecommerce` 物理隔离；`alembic downgrade`
  只允许在测试库执行（已写入 CI 习惯与测试守卫）。

## Phase 1 边界（刻意未做）

DeepSeek 真实调用、SSE 流式回复、WeKnora/MinIO/Langfuse、支付/退款/物流、
Multi-Agent 编排——全部留给 Phase 2。
