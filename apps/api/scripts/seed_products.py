"""向数据库写入示例商品（仅当 products 表为空时执行）。

用法（开发库）:
  DATABASE_URL="postgresql+asyncpg://ecommerce:<password>@127.0.0.1:55432/ecommerce" \
    uv run python scripts/seed_products.py
"""
import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select

from app.core.database import SessionFactory
from app.models import Product

SAMPLE_PRODUCTS = [
    ("无线蓝牙降噪耳机 Pro", "主动降噪，30 小时续航，支持快充", Decimal("399.00"), 120),
    ("智能手表 S6", "血氧监测，14 天续航，50 米防水", Decimal("899.00"), 80),
    ("机械键盘 87 键", "热插拔轴体，RGB 背光，三模连接", Decimal("499.00"), 60),
    ("便携充电宝 20000mAh", "65W 快充，双向 Type-C", Decimal("159.00"), 200),
    ("人体工学椅", "腰托支撑，透气网布，可调节扶手", Decimal("1299.00"), 30),
]


async def main() -> None:
    async with SessionFactory() as session:
        count = await session.scalar(select(func.count()).select_from(Product))
        if count:
            print(f"products 已有 {count} 条记录，跳过 seed")
            return
        session.add_all(
            Product(name=name, description=desc, price=price, stock=stock)
            for name, desc, price, stock in SAMPLE_PRODUCTS
        )
        await session.commit()
        print(f"已写入 {len(SAMPLE_PRODUCTS)} 条示例商品")


if __name__ == "__main__":
    asyncio.run(main())
