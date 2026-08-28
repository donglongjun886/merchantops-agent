"""4 个业务模型：商品 / 订单 / 订单明细 / 任务。

约定：
- 状态用普通字符串列，不用 SQLAlchemy Enum（简单、好查、好改）
- 外键只建在 order_item（order_no -> merchant_order.order_no、product_sku -> product.sku）
- task.related_order_no 只建普通索引，不强制外键
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Product(Base):
    """商品。"""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64))
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    stock: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MerchantOrder(Base):
    """商家订单。"""

    __tablename__ = "merchant_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # 枚举值：PENDING/PAID/SHIPPED/COMPLETED/CANCELLED/REFUNDED/RISK_REVIEW
    status: Mapped[str] = mapped_column(String(16))
    buyer_name: Mapped[str | None] = mapped_column(String(64))
    buyer_phone: Mapped[str | None] = mapped_column(String(20))
    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OrderItem(Base):
    """订单明细（1 个订单 N 条明细）。"""

    __tablename__ = "order_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("merchant_order.order_no"),
        index=True,
        nullable=False,
    )
    product_sku: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("product.sku"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[float | None] = mapped_column(Numeric(10, 2))


class Task(Base):
    """任务（含跨域关联：related_order_no 指向订单号）。"""

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    related_order_no: Mapped[str | None] = mapped_column(String(32), index=True)
    # 枚举值：PENDING/IN_PROGRESS/COMPLETED/CANCELLED
    status: Mapped[str] = mapped_column(String(16))
    owner: Mapped[str | None] = mapped_column(String(64))
    # 枚举值：LOW/MEDIUM/HIGH/URGENT
    priority: Mapped[str | None] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # updated_at 手动维护，不用事件监听
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
