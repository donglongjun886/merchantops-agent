"""4 个业务模型：商家 / 经营任务 / 任务进度 / 商家订单。

表关系：
- merchant 1:N task（task.merchant_id -> merchant.id）
- merchant 1:N merchant_order（merchant_order.merchant_id -> merchant.id）
- task 1:N task_progress（task_progress.task_id -> task.id）

约定：
- 状态、指标类型用普通字符串列，不用 SQLAlchemy Enum（简单、好查、好改）
- created_at 用 server_default=func.now()；updated_at、completed_at 可空、手动维护（不用事件监听）
- merchant_order 没有 updated_at，其他三张有
- 2.0 风格 Mapped + mapped_column；不建 relationship、不用 async、不用 alembic
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Merchant(Base):
    """商家。"""

    __tablename__ = "merchant"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 状态：ACTIVE / INACTIVE
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # updated_at 手动维护，不用事件监听
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class Task(Base):
    """经营任务。"""

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("merchant.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 指标类型：GMV / ORDER_COUNT
    metric_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    # 状态：PENDING / IN_PROGRESS / COMPLETED / CANCELLED
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # updated_at 手动维护，不用事件监听
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class TaskProgress(Base):
    """任务进度。"""

    __tablename__ = "task_progress"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("task.id"), index=True, nullable=False
    )
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # 完成百分比 0-100.00
    progress: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    # 状态：IN_PROGRESS / COMPLETED
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    # 仅任务完成时有值
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # updated_at 手动维护，不用事件监听
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class MerchantOrder(Base):
    """商家订单。"""

    __tablename__ = "merchant_order"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # 业务订单号
    order_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    merchant_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("merchant.id"), index=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # 状态：PENDING/PAID/SHIPPED/COMPLETED/CANCELLED/REFUNDED/RISK_REVIEW（贴风控场景）
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
