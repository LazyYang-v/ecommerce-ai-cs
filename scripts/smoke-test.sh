#!/usr/bin/env bash
# Phase 1 冒烟测试：针对真实容器与真实 HTTP 服务的端到端断言（非 mock）。
# 前置条件: docker compose up -d 已启动、迁移已执行、商品 seed 已运行。
# 用法: ./scripts/smoke-test.sh
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

API=http://127.0.0.1:8000
AGENT=http://127.0.0.1:8001
V1=$API/api/v1
TS="$(date +%s)$RANDOM"
REQ_ID="smoke-$TS"
TOKEN="$(sed -n 's/^INTERNAL_SERVICE_TOKEN=//p' .env)"

if [[ -z "$TOKEN" ]]; then
  echo "缺少 INTERNAL_SERVICE_TOKEN（.env）" >&2
  exit 2
fi

PASS=0
FAIL=0
ok() {
  PASS=$((PASS + 1))
  echo "  [PASS] $1"
}
bad() {
  FAIL=$((FAIL + 1))
  echo "  [FAIL] $1"
}
expect_code() { # expect_code 描述 期望 实际
  if [[ "$2" == "$3" ]]; then
    ok "$1 ($3)"
  else
    bad "$1（期望 $2，实际 $3）body: $(head -c 200 "$LAST_BODY_FILE" 2>/dev/null)"
  fi
}
LAST_BODY_FILE="$(mktemp)"
code() { # code METHOD URL [BODY] [EXTRA_HEADER] -> HTTP 状态码
  local method=$1 url=$2 body=${3:-} extra=${4:-}
  local args=(-s -o "$LAST_BODY_FILE" -w '%{http_code}' -X "$method" "$url" -H 'Content-Type: application/json')
  [[ -n "$extra" ]] && args+=(-H "$extra")
  [[ -n "$body" ]] && args+=(-d "$body")
  curl "${args[@]}"
}
json_field() { # json_field <json字符串> <字段>
  python3 -c "import json,sys; print(json.load(sys.stdin).get('$2',''))" <<<"$1"
}

echo "== 1. 容器健康 =="
for svc in postgres redis api agent; do
  line="$(docker compose ps --format '{{.Service}} {{.Status}}' "$svc" 2>/dev/null | head -1)"
  if echo "$line" | grep -q '(healthy)'; then ok "$svc: $line"; else bad "$svc: ${line:-未找到}"; fi
done

echo "== 2. 服务健康检查 =="
expect_code "Business API /health" 200 "$(code GET "$API/health")"
expect_code "Agent /health" 200 "$(code GET "$AGENT/health")"

echo "== 3. Agent 内部令牌鉴权 =="
expect_code "Agent 无令牌 → 401" 401 "$(code POST "$AGENT/internal/chat" '{"message":"ping"}')"
expect_code "Agent 错误令牌 → 401" 401 \
  "$(code POST "$AGENT/internal/chat" '{"message":"ping"}' "X-Internal-Token: wrong-token")"
expect_code "Agent 正确令牌 → 200" 200 \
  "$(code POST "$AGENT/internal/chat" '{"message":"ping"}' "X-Internal-Token: $TOKEN")"

echo "== 4. 全链路（客户端 → API → Agent → API → 客户端） =="
headers="$(mktemp)"
body="$(curl -s -D "$headers" -X POST "$V1/chat/test" \
  -H 'Content-Type: application/json' -H "X-Request-ID: $REQ_ID" \
  -d '{"message":"全链路冒烟"}')"
status="$(awk 'NR==1{print $2}' "$headers")"
expect_code "全链路状态码" 200 "$status"
if echo "$body" | grep -q "已收到消息：全链路冒烟"; then ok "Agent 响应回显"; else bad "响应内容: $body"; fi
hdr_rid="$(grep -i '^x-request-id:' "$headers" | tr -d '\r' | awk '{print $2}')"
if [[ "$hdr_rid" == "$REQ_ID" ]]; then ok "响应头 X-Request-ID 回传"; else bad "响应头 X-Request-ID: $hdr_rid"; fi
body_rid="$(json_field "$body" request_id)"
if [[ "$body_rid" == "$REQ_ID" ]]; then ok "响应体 request_id 回传"; else bad "响应体 request_id: $body_rid"; fi
rm -f "$headers"

echo "== 5. request_id 贯穿两侧日志 =="
if docker compose logs api --since 5m 2>&1 | grep -qF "[$REQ_ID]"; then
  ok "api 日志包含 $REQ_ID"
else
  bad "api 日志未找到 $REQ_ID"
fi
if docker compose logs agent --since 5m 2>&1 | grep -qF "[$REQ_ID]"; then
  ok "agent 日志包含 $REQ_ID"
else
  bad "agent 日志未找到 $REQ_ID"
fi

echo "== 6. 业务接口（真实数据库） =="
expect_code "GET /products" 200 "$(code GET "$V1/products")"
total="$(curl -s "$V1/products" | python3 -c 'import json,sys; print(json.load(sys.stdin)["total"])')"
if [[ "$total" =~ ^[0-9]+$ ]] && [[ "$total" -ge 1 ]]; then ok "商品 seed 存在（total=${total}）"; else bad "商品列表为空（total=${total}），请先运行 seed"; fi
email_a="smoke-a-$TS@test.com"
email_b="smoke-b-$TS@test.com"
reg_body_a="$(printf '{"email":"%s","password":"password123"}' "$email_a")"
reg_body_b="$(printf '{"email":"%s","password":"password123"}' "$email_b")"
login_body_a="$(printf '{"email":"%s","password":"password123"}' "$email_a")"
login_body_b="$(printf '{"email":"%s","password":"password123"}' "$email_b")"
login_body_bad="$(printf '{"email":"%s","password":"wrong-pass"}' "$email_a")"
expect_code "注册用户 A" 201 "$(code POST "$V1/auth/register" "$reg_body_a")"
expect_code "注册用户 B" 201 "$(code POST "$V1/auth/register" "$reg_body_b")"
token_a="$(json_field "$(curl -s -X POST "$V1/auth/login" -H 'Content-Type: application/json' -d "$login_body_a")" access_token)"
token_b="$(json_field "$(curl -s -X POST "$V1/auth/login" -H 'Content-Type: application/json' -d "$login_body_b")" access_token)"
if [[ -n "$token_a" && -n "$token_b" ]]; then ok "登录签发 JWT"; else bad "登录失败"; fi
expect_code "错误密码登录 → 401" 401 "$(code POST "$V1/auth/login" "$login_body_bad")"
conv_id="$(json_field "$(curl -s -X POST "$V1/conversations" -H "Authorization: Bearer $token_a")" id)"
if [[ -n "$conv_id" ]]; then ok "A 创建会话"; else bad "A 创建会话失败"; fi
expect_code "A 读自己会话消息 → 200" 200 \
  "$(code GET "$V1/conversations/$conv_id/messages" "" "Authorization: Bearer $token_a")"
expect_code "B 读 A 会话消息 → 404（越权拦截）" 404 \
  "$(code GET "$V1/conversations/$conv_id/messages" "" "Authorization: Bearer $token_b")"
expect_code "无 token 列订单 → 401" 401 "$(code GET "$V1/orders")"

echo "== 7. 数据库迁移状态（宿主机执行，容器镜像不含迁移脚本） =="
DEV_DB_URL="postgresql+asyncpg://ecommerce:$(sed -n 's/^POSTGRES_PASSWORD=//p' .env)@127.0.0.1:55432/ecommerce"
rev="$(cd apps/api && DATABASE_URL="$DEV_DB_URL" uv run alembic current 2>/dev/null | tail -1)"
if [[ "$rev" == *"(head)"* ]]; then ok "alembic current: $rev"; else bad "alembic current: ${rev:-空}"; fi

echo "== 8. Agent 故障降级（停止 → 502 → 恢复） =="
docker compose stop agent >/dev/null 2>&1
expect_code "Agent 停止时全链路 → 502" 502 "$(code POST "$V1/chat/test" '{"message":"ping"}')"
docker compose start agent >/dev/null 2>&1
curl -s --retry 30 --retry-delay 1 --retry-connrefused -o /dev/null "$AGENT/health"
recovered=""
for _ in 1 2 3; do
  recovered="$(code POST "$V1/chat/test" '{"message":"恢复后重试"}')"
  [[ "$recovered" == 200 ]] && break
done
expect_code "Agent 恢复后全链路 → 200" 200 "$recovered"

echo
echo "======== 冒烟结果: PASS=$PASS FAIL=$FAIL ========"
if [[ "$FAIL" -ne 0 ]]; then exit 1; fi
