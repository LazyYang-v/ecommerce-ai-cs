# packages/contracts

存放服务间 API 契约：Business API ↔ Agent Service 的内部接口定义、对外 REST 接口的请求/响应 Schema。

Phase 1 约定：

- 服务间通信契约以 `docs/api-contracts.md` 为准（含 `X-Internal-Token` 鉴权、`X-Request-ID` 透传、超时与错误语义）。
- Agent 请求/响应 Schema 预留 `conversation_id`、`thread_id`、`request_id` 字段，为后续 LangGraph 持久化（checkpointer / thread）做准备。
- 后续如需代码级共享 Schema，可在此包内维护 OpenAPI 规范或 Python 包，由两个服务共同引用，避免契约漂移。
