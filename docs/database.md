# 数据库设计（Phase 1）

PostgreSQL 17，六张核心表，全部由 Alembic 迁移管理（`apps/api/alembic/`）。
**禁止** `Base.metadata.create_all()` 式建表。

## 通用约定

- 主键：`UUID`（应用侧 `uuid4` 生成）。
- 金额：`NUMERIC(12,2)`，Python 侧 `Decimal`，JSON 序列化为字符串（如 `"399.00"`）。
- 时间：`TIMESTAMPTZ`（内部按 UTC 存储），`created_at`/`updated_at` 由数据库
  `now()` 默认值维护。
- 约束/索引全部显式命名（`pk_` / `fk_` / `uq_` / `ck_` / `ix_` 前缀），保证迁移可回滚。
- 枚举使用 PostgreSQL 原生 `CREATE TYPE`，取值为小写下划线串。

## 表结构

### users — 用户与身份

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| email | varchar(255) | **唯一**（`uq_users_email`，应用侧统一小写） |
| password_hash | varchar(255) | 非 null，argon2 哈希，绝不存明文 |
| nickname | varchar(64) | 可空 |
| role | userrole | `customer / staff / admin`，默认 customer |
| is_active | boolean | 默认 true |
| created_at / updated_at | timestamptz | |

### products — 商品

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| name | varchar(200) | |
| description | text | 可空 |
| price | numeric(12,2) | |
| stock | integer | `ck_products_stock_non_negative (stock >= 0)` |
| status | productstatus | `on_sale / off_sale`，**索引** `ix_products_status` |

### orders — 订单

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK → users.id |
| status | orderstatus | `pending_payment / paid / shipped / completed / cancelled` |
| total_amount | numeric(12,2) | |
| created_at / updated_at | timestamptz | |

索引：`ix_orders_user_id_created_at (user_id, created_at)`（我的订单列表按时间倒序）。

### order_items — 订单明细（含快照）

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| order_id | uuid | FK → orders.id，索引 `ix_order_items_order_id` |
| product_id | uuid | FK → products.id |
| **product_name** | varchar(200) | 下单时快照：防商品改名影响历史订单 |
| **unit_price** | numeric(12,2) | 下单时快照：防改价影响历史订单 |
| quantity | integer | `ck_order_items_quantity_positive (quantity > 0)` |

### conversations — 客服会话

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK → users.id，索引 `ix_conversations_user_id` |
| status | conversationstatus | `open / closed`，默认 open |

**刻意不绑定单个 `order_id`**：一次会话可能涉及多个订单，后续如需关联新增
`conversation_orders` 关联表（`infra/postgres/` 预留）。

### messages — 对话消息（不可变，无 updated_at）

| 列 | 类型 | 约束 |
|---|---|---|
| id | uuid | PK |
| conversation_id | uuid | FK → conversations.id |
| sender_type | messagesendertype | `user / agent / human_agent / system` |
| content | text | |
| created_at | timestamptz | |

索引：`ix_messages_conversation_id_created_at (conversation_id, created_at)`（按时间正序分页）。

## 迁移工作流

```bash
cd apps/api
export DATABASE_URL="postgresql+asyncpg://ecommerce:<pw>@127.0.0.1:55432/ecommerce"

uv run alembic revision --autogenerate -m "..."   # 生成后必须人工审查 SQL
uv run alembic upgrade head                        # 应用
uv run alembic current                             # 确认版本
```

连接串只从环境变量读取，密码不进入任何版本库文件。

## 测试库隔离（硬性要求）

- 开发库 `ecommerce`，测试库 `ecommerce_test`，同一实例内物理隔离。
- pytest 的 `tests/conftest.py` 含强制守卫：`DATABASE_URL` 不含 `ecommerce_test`
  则直接拒绝运行。
- 每个测试用例结束后 TRUNCATE 全部业务表（测试引擎使用 NullPool 跨事件循环安全）。
- **`alembic downgrade` 只允许在 `ecommerce_test` 上执行**，开发库永不降级。

## 已知坑（已修复并验证）

Alembic 自动生成的 `downgrade` **不会**删除随 `create_table` 创建的 PG 枚举类型，
导致降级后再次升级报 `DuplicateObjectError`。初始迁移的 downgrade 已显式
`sa.Enum(name=...).drop(checkfirst=True)`，并在测试库完成
升级 → 降级 → 升级 完整循环验证。
