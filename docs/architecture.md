# 系统架构（Phase 1）

## 服务与职责

| 服务 | 技术栈 | 职责 | 端口（宿主机均 127.0.0.1） |
|---|---|---|---|
| web | React 19 + TypeScript + Vite + antd | 商品浏览、客服链路测试页 | 5173（dev） |
| api | Python 3.12 + FastAPI + SQLAlchemy 2 | 鉴权、业务规则、订单/会话、工具网关、数据持久化 | 8000 |
| agent | Python 3.12 + FastAPI + LangGraph | 对话状态与 Agent 编排（Phase 1 为确定性测试图） | 8001 |
| postgres | PostgreSQL 17 | 业务数据 | 55432 → 5432 |
| redis | Redis 7 | 缓存/限流预留 | 56379 → 6379 |

## 架构约束

1. **前端只调用 Business API**。开发期由 Vite 代理 `/api` → `127.0.0.1:8000`；
   生产由反向代理承担。前端代码中不存在 Agent 地址。
2. **Agent 不直接读写业务数据库**。Phase 2 的订单查询等工具将经 Business API
   提供的受控内部接口（携带 `X-Internal-Token` 与用户上下文）访问，避免绕过
   权限校验与业务规则。业务写操作永远不允许由 LLM 直接执行。
3. **内部服务互信**：`INTERNAL_SERVICE_TOKEN` 双方共享，接收方用
   `secrets.compare_digest` 常量时间比较；令牌未配置时 fail-closed（全部拒绝）。
4. **PostgreSQL / Redis / Agent 的宿主机端口仅绑定回环地址**；生产环境 Agent
   与数据层不暴露公网。

## 通信矩阵

| 调用方 | 接收方 | 协议 | 鉴权 | 说明 |
|---|---|---|---|---|
| React | Business API | HTTP/JSON | 用户 JWT（业务接口） | Vite 代理 |
| Business API | Agent | HTTP/JSON | X-Internal-Token | HTTPX，超时 15s，连接级重试 ×2 |
| Agent | Business API | HTTP/JSON | X-Internal-Token | Phase 2 启用（工具调用） |
| Business API | PostgreSQL | SQL（asyncpg） | 密码 | compose 内网 |
| Business API | Redis | Redis 协议 | — | Phase 1 未使用 |
| Agent | DeepSeek | HTTPS | API Key | Phase 2 |

## 请求全链路与可观测性

每个入站请求：

1. API 中间件读取 `X-Request-ID`，缺失则生成 `uuid4().hex`；
2. request_id 注入日志（ContextVar + logging Filter，格式 `[request_id]`）；
3. API → Agent 的 HTTPX 调用透传 `X-Request-ID` 头，同时放入请求体 `request_id`；
4. Agent 侧同样回填响应头与响应体；
5. 两侧服务日志可用同一 request_id 串联（`docker compose logs` + grep）。

日志红线：不输出密码、密码哈希、内部令牌、JWT；消息内容只记长度。

## 错误语义

| 场景 | 对外行为 |
|---|---|
| Agent 网络错误/超时/非 2xx | API 统一 `502 {"detail":"Agent service unavailable"}` |
| 内部令牌缺失/错误 | `401`（Agent 侧拒绝；API 侧视为上游故障 → 502） |
| 资源不存在 **或** 属于他人 | `404`（不泄露存在性） |
| 未携带/无效 JWT | `401` + `WWW-Authenticate: Bearer` |

## 部署形态（开发）

- `compose.yaml`：4 服务全部配置 healthcheck（pg_isready / redis-cli ping / 自身
  `/health`），api 依赖 postgres+redis healthy 后启动。
- 网络：本项目固定子网 `10.99.0.0/24`（本机地址池耗尽的规避，见 README）。
- 镜像：`python:3.12-slim` + 固定版本 `uv 0.12.3`，非 root 用户运行，依赖层与
  代码层分离。迁移脚本不进镜像，由宿主机执行（正式部署时可引入 init 容器）。

## Phase 2 展望（不改 Phase 1 契约）

- Agent 接入 DeepSeek（`langchain-openai` 已就位），`customer_graph` 替换为真实
  模型节点，引入 checkpointer 时直接使用已预留的 `thread_id`；
- Agent → Business API 受控工具（只读订单/物流查询）；
- SSE 流式回复、会话消息持久化（表已就绪）、限流（Redis）。
