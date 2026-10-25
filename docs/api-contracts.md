# API 契约（Phase 1）

对外 REST 由 **Business API**（`:8000`）提供，OpenAPI 文档：
`http://localhost:8000/docs`（Swagger UI，可直接调试）。

通用约定：

- 认证接口外，业务接口需 `Authorization: Bearer <JWT>`。
- 分页参数 `page`（≥1）、`page_size`（1–100，默认 20）；响应包裹
  `{items, total, page, page_size}`。
- **金额一律字符串**（`"399.00"`），时间一律 UTC ISO-8601（`2026-10-25T12:53:09Z`）。
- 每个响应带 `X-Request-ID` 头（入站有则透传，无则生成）。
- 错误体：`{"detail": "..."}`；资源不存在或属于他人 → `404`（不泄露存在性）。

## 对外接口

### 认证

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/v1/auth/register` | 无 | `{email, password(≥8), nickname?}` → 201 用户信息；重复邮箱 409 |
| POST | `/api/v1/auth/login` | 无 | `{email, password}` → `{access_token, token_type:"bearer", expires_in}`；凭据错误 401 |
| GET | `/api/v1/auth/me` | Bearer | 当前用户信息（补充端点） |

### 商品（公开）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/products` | 仅 `on_sale`，分页 |
| GET | `/api/v1/products/{id}` | 非 `on_sale` 或不存在 → 404 |

```json
{"id":"uuid","name":"…","description":null,"price":"399.00","stock":120,
 "status":"on_sale","created_at":"2026-10-25T12:53:09Z"}
```

### 订单（需登录，仅本人）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/orders` | 本人订单分页（摘要，无明细） |
| GET | `/api/v1/orders/{id}` | 详情含 `items[]`（`product_name`、`unit_price` 为下单快照）；他人订单 → 404 |

### 会话（需登录，仅本人）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/conversations` | 创建 `open` 会话 → 201 |
| GET | `/api/v1/conversations` | 本人会话分页 |
| GET | `/api/v1/conversations/{id}/messages` | 消息按时间正序分页（默认 page_size=50）；他人会话 → 404 |

```json
{"id":"uuid","sender_type":"user|agent|human_agent|system","content":"…","created_at":"…"}
```

### Phase 1 通信验收（开发专用）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/chat/test` | `{message(1–2000)}` → 转发 Agent 并原样返回；Agent 故障 → 502。正式客服接口（鉴权+持久化）Phase 2 |

## 内部契约：Business API ↔ Agent Service

`POST {AGENT_URL}/internal/chat`（Agent `:8001`，仅容器网络 + 本机回环可达）

**请求头**

| 头 | 必填 | 说明 |
|---|---|---|
| `X-Internal-Token` | 是 | 共享内部令牌；错误/缺失 → 401（`compare_digest`，未配置时 fail-closed） |
| `X-Request-ID` | 建议 | 链路追踪 ID（uuid4 hex） |
| `Content-Type` | 是 | `application/json` |

**请求体**

```json
{
  "message": "用户消息（1–2000 字符）",
  "conversation_id": null,
  "thread_id": null,
  "request_id": null
}
```

`conversation_id` / `thread_id` / `request_id` 为 Phase 2 预留（LangGraph
checkpointer 按 thread 持久化、全链路追踪），Phase 1 可全部缺省。

**响应体**（200）

```json
{
  "response": "已收到消息：<message>",
  "conversation_id": null,
  "thread_id": null,
  "request_id": "<回传实际使用的 request_id>"
}
```

Phase 1 的 `response` 为 LangGraph 最小图的**确定性测试响应**，不代表 LLM 推理。

**语义与超时**

- API 侧 HTTPX 超时 15s（`AGENT_TIMEOUT_SECONDS` 可调），连接级重试 ×2；
- Agent 任何网络错误/超时/非 2xx → API 对外统一 `502 Agent service unavailable`；
- `GET /health` 两服务均公开，供 compose healthcheck 使用。
