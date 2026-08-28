"""建表 + 灌 seed 数据（可重复执行：先 drop 再 create，然后插入）。

四张新表：merchant / task / task_progress / merchant_order。
旧表 product / order_item 会被 drop，属于预期的整体替换。

数据自洽性说明：
- 星辰数码旗舰店（IN_PROGRESS 的 GMV 任务）的 task_progress.current_value = 48295.00，
  恰好等于该商家全部订单 amount 之和（21999+15998+1299+8999 = 48295.00），
  后续 Agent 查"GMV 完成度"能对上账。
- 悦动运动专营店同理：current_value = 7200.00 = 全部订单金额之和（1800+2698+902+1800）。
"""

from datetime import datetime

from sqlalchemy import text

from app.db.base import Base
from app.db.models import Merchant, MerchantOrder, Task, TaskProgress
from app.db.session import SessionLocal, engine


def seed() -> None:
    # 幂等：删表重建
    # 旧 schema 遗留表 product / order_item 不在新 metadata 里，drop_all 不会删；
    # 且 order_item 外键仍指向旧 merchant_order，不先清掉会挡 drop_all（整体替换的预期动作）
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("DROP TABLE IF EXISTS order_item"))
        conn.execute(text("DROP TABLE IF EXISTS product"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    merchants = [
        Merchant(name="星辰数码旗舰店", status="ACTIVE", created_at=datetime(2025, 1, 15, 9, 0), updated_at=datetime(2025, 8, 20, 10, 0)),
        Merchant(name="悦动运动专营店", status="ACTIVE", created_at=datetime(2025, 2, 10, 9, 0), updated_at=datetime(2025, 8, 18, 10, 0)),
        Merchant(name="拾光服饰", status="INACTIVE", created_at=datetime(2025, 3, 1, 9, 0), updated_at=datetime(2025, 7, 31, 18, 0)),
        Merchant(name="味蕾食品", status="ACTIVE", created_at=datetime(2025, 4, 20, 9, 0), updated_at=datetime(2025, 8, 15, 10, 0)),
    ]

    tasks = [
        Task(merchant_id=1, name="本月GMV目标", metric_type="GMV", target_value="80000.00",
             start_time=datetime(2025, 8, 1, 0, 0), end_time=datetime(2025, 8, 31, 23, 59),
             status="IN_PROGRESS", created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 27, 9, 0)),
        Task(merchant_id=1, name="本月订单量目标", metric_type="ORDER_COUNT", target_value="300",
             start_time=datetime(2025, 8, 1, 0, 0), end_time=datetime(2025, 8, 31, 23, 59),
             status="COMPLETED", created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 25, 18, 0)),
        Task(merchant_id=2, name="本月GMV目标", metric_type="GMV", target_value="20000.00",
             start_time=datetime(2025, 8, 1, 0, 0), end_time=datetime(2025, 8, 31, 23, 59),
             status="IN_PROGRESS", created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 27, 10, 30)),
        Task(merchant_id=3, name="上月GMV目标", metric_type="GMV", target_value="50000.00",
             start_time=datetime(2025, 7, 1, 0, 0), end_time=datetime(2025, 7, 31, 23, 59),
             status="COMPLETED", created_at=datetime(2025, 7, 1, 9, 0), updated_at=datetime(2025, 8, 1, 10, 0)),
        Task(merchant_id=4, name="本月订单量目标", metric_type="ORDER_COUNT", target_value="200",
             start_time=datetime(2025, 8, 1, 0, 0), end_time=datetime(2025, 8, 31, 23, 59),
             status="PENDING", created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 27, 11, 0)),
        Task(merchant_id=4, name="上月GMV目标", metric_type="GMV", target_value="60000.00",
             start_time=datetime(2025, 7, 1, 0, 0), end_time=datetime(2025, 7, 31, 23, 59),
             status="COMPLETED", created_at=datetime(2025, 7, 1, 9, 0), updated_at=datetime(2025, 8, 1, 9, 30)),
    ]

    # current_value 与订单金额之和自洽（见文件头注释）
    task_progress = [
        TaskProgress(task_id=1, current_value="48295.00", progress="60.37", status="IN_PROGRESS",
                     completed_at=None, created_at=datetime(2025, 8, 5, 9, 0), updated_at=datetime(2025, 8, 27, 9, 0)),
        TaskProgress(task_id=2, current_value="300.00", progress="100.00", status="COMPLETED",
                     completed_at=datetime(2025, 8, 25, 18, 0), created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 25, 18, 0)),
        TaskProgress(task_id=3, current_value="7200.00", progress="36.00", status="IN_PROGRESS",
                     completed_at=None, created_at=datetime(2025, 8, 5, 9, 0), updated_at=datetime(2025, 8, 27, 10, 30)),
        TaskProgress(task_id=4, current_value="50000.00", progress="100.00", status="COMPLETED",
                     completed_at=datetime(2025, 8, 1, 10, 0), created_at=datetime(2025, 7, 5, 9, 0), updated_at=datetime(2025, 8, 1, 10, 0)),
        TaskProgress(task_id=5, current_value="0.00", progress="0.00", status="IN_PROGRESS",
                     completed_at=None, created_at=datetime(2025, 8, 1, 9, 0), updated_at=datetime(2025, 8, 27, 11, 0)),
        TaskProgress(task_id=6, current_value="60000.00", progress="100.00", status="COMPLETED",
                     completed_at=datetime(2025, 8, 1, 9, 30), created_at=datetime(2025, 7, 5, 9, 0), updated_at=datetime(2025, 8, 1, 9, 30)),
    ]

    orders = [
        # 星辰数码旗舰店（合计 48295.00，对得上 task 1 的 current_value）
        MerchantOrder(order_id="XD20250801001", merchant_id=1, amount="21999.00", status="PAID", created_at=datetime(2025, 8, 3, 10, 21)),
        MerchantOrder(order_id="XD20250801002", merchant_id=1, amount="15998.00", status="SHIPPED", created_at=datetime(2025, 8, 11, 14, 5)),
        MerchantOrder(order_id="XD20250801003", merchant_id=1, amount="1299.00", status="RISK_REVIEW", created_at=datetime(2025, 8, 19, 23, 47)),
        MerchantOrder(order_id="XD20250801004", merchant_id=1, amount="8999.00", status="COMPLETED", created_at=datetime(2025, 8, 26, 9, 12)),
        # 悦动运动专营店（合计 7200.00，对得上 task 3 的 current_value）
        MerchantOrder(order_id="YD20250802001", merchant_id=2, amount="1800.00", status="PAID", created_at=datetime(2025, 8, 4, 9, 30)),
        MerchantOrder(order_id="YD20250802002", merchant_id=2, amount="2698.00", status="SHIPPED", created_at=datetime(2025, 8, 15, 16, 20)),
        MerchantOrder(order_id="YD20250802003", merchant_id=2, amount="902.00", status="REFUNDED", created_at=datetime(2025, 8, 20, 11, 8)),
        MerchantOrder(order_id="YD20250802004", merchant_id=2, amount="1800.00", status="COMPLETED", created_at=datetime(2025, 8, 26, 15, 44)),
        # 拾光服饰（上月订单）
        MerchantOrder(order_id="SG20250703001", merchant_id=3, amount="596.00", status="COMPLETED", created_at=datetime(2025, 7, 6, 12, 0)),
        MerchantOrder(order_id="SG20250703002", merchant_id=3, amount="397.00", status="REFUNDED", created_at=datetime(2025, 7, 15, 19, 30)),
        MerchantOrder(order_id="SG20250703003", merchant_id=3, amount="795.00", status="CANCELLED", created_at=datetime(2025, 7, 21, 8, 55)),
        # 味蕾食品
        MerchantOrder(order_id="WL20250804001", merchant_id=4, amount="258.00", status="PAID", created_at=datetime(2025, 8, 5, 20, 15)),
        MerchantOrder(order_id="WL20250804002", merchant_id=4, amount="516.00", status="COMPLETED", created_at=datetime(2025, 8, 14, 12, 40)),
        MerchantOrder(order_id="WL20250804003", merchant_id=4, amount="129.00", status="PENDING", created_at=datetime(2025, 8, 25, 22, 31)),
        MerchantOrder(order_id="WL20250804004", merchant_id=4, amount="387.00", status="COMPLETED", created_at=datetime(2025, 8, 26, 18, 2)),
    ]

    with SessionLocal() as session:
        session.add_all(merchants)
        session.flush()  # 先落商家拿 id
        session.add_all(tasks)
        session.flush()  # 再落任务拿 id
        session.add_all(task_progress)
        session.add_all(orders)
        session.commit()

        counts = {
            "merchant": session.query(Merchant).count(),
            "task": session.query(Task).count(),
            "task_progress": session.query(TaskProgress).count(),
            "merchant_order": session.query(MerchantOrder).count(),
        }
        for table, count in counts.items():
            print(f"seed: {table} 插入 {count} 行")


if __name__ == "__main__":
    seed()
