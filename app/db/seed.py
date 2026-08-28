"""建表 + 灌 seed 数据（可重复执行：先 drop 再 create，然后插入）。"""

from datetime import datetime

from app.db.base import Base
from app.db.models import MerchantOrder, OrderItem, Product, Task
from app.db.session import SessionLocal, engine


def seed() -> None:
    # 幂等：删表重建
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    products = [
        Product(sku="SKU1001", name="iPhone 15 Pro 256G", category="手机", price="9999.00", stock=50, status="ACTIVE"),
        Product(sku="SKU1002", name="华为 FreeBuds Pro 3 降噪耳机", category="耳机", price="1499.00", stock=120, status="ACTIVE"),
        Product(sku="SKU1003", name="安克 10000mAh 充电宝", category="充电宝", price="129.00", stock=300, status="ACTIVE"),
        Product(sku="SKU1004", name="耐克 Air Max 90 运动鞋", category="鞋", price="899.00", stock=80, status="ACTIVE"),
        Product(sku="SKU1005", name="优衣库 摇粒绒外套", category="衣服", price="199.00", stock=200, status="ACTIVE"),
        Product(sku="SKU1006", name="小米 67W 氮化镓充电器", category="配件", price="79.00", stock=500, status="ACTIVE"),
    ]

    orders = [
        MerchantOrder(order_no="1001", status="PAID", buyer_name="张三", buyer_phone="13800000001", total_amount="11577.00", created_at=datetime(2025, 8, 25, 10, 30)),
        MerchantOrder(order_no="1002", status="SHIPPED", buyer_name="李四", buyer_phone="13800000002", total_amount="1997.00", created_at=datetime(2025, 8, 25, 14, 5)),
        MerchantOrder(order_no="1003", status="RISK_REVIEW", buyer_name="王五", buyer_phone="13800000003", total_amount="3385.00", created_at=datetime(2025, 8, 26, 9, 20)),
        MerchantOrder(order_no="1004", status="PENDING", buyer_name="赵六", buyer_phone="13800000004", total_amount="803.00", created_at=datetime(2025, 8, 26, 20, 45)),
    ]

    # 明细金额与 total_amount 严格一致：sum(subtotal) == total_amount
    items = [
        OrderItem(order_no="1001", product_sku="SKU1001", quantity=1, unit_price="9999.00", subtotal="9999.00"),
        OrderItem(order_no="1001", product_sku="SKU1002", quantity=1, unit_price="1499.00", subtotal="1499.00"),
        OrderItem(order_no="1001", product_sku="SKU1006", quantity=1, unit_price="79.00", subtotal="79.00"),
        OrderItem(order_no="1002", product_sku="SKU1004", quantity=2, unit_price="899.00", subtotal="1798.00"),
        OrderItem(order_no="1002", product_sku="SKU1005", quantity=1, unit_price="199.00", subtotal="199.00"),
        OrderItem(order_no="1003", product_sku="SKU1002", quantity=2, unit_price="1499.00", subtotal="2998.00"),
        OrderItem(order_no="1003", product_sku="SKU1003", quantity=3, unit_price="129.00", subtotal="387.00"),
        OrderItem(order_no="1004", product_sku="SKU1003", quantity=5, unit_price="129.00", subtotal="645.00"),
        OrderItem(order_no="1004", product_sku="SKU1006", quantity=2, unit_price="79.00", subtotal="158.00"),
    ]

    tasks = [
        Task(task_no="T1001", title="订单 1001 风控人工复核", related_order_no="1001", status="PENDING", owner="风控组", priority="URGENT", updated_at=datetime(2025, 8, 25, 11, 0)),
        Task(task_no="T1002", title="订单 1003 高风险交易人工审核", related_order_no="1003", status="IN_PROGRESS", owner="风控组", priority="HIGH", updated_at=datetime(2025, 8, 26, 10, 0)),
        Task(task_no="T1003", title="处理退款申请：订单 1004 买家取消", related_order_no="1004", status="PENDING", owner="客服组", priority="MEDIUM", updated_at=datetime(2025, 8, 26, 21, 0)),
        Task(task_no="T1004", title="核对 1002 订单发货物流单号", related_order_no="1002", status="COMPLETED", owner="仓储组", priority="LOW", updated_at=datetime(2025, 8, 25, 18, 30)),
        Task(task_no="T1005", title="每周库存盘点（手机类目）", related_order_no=None, status="PENDING", owner="运营组", priority="MEDIUM", updated_at=datetime(2025, 8, 27, 9, 0)),
    ]

    with SessionLocal() as session:
        session.add_all(products)
        session.add_all(orders)
        # 先落商品和订单，order_item 的外键依赖它们（ORM 没定义 relationship，需手动控制插入顺序）
        session.flush()
        session.add_all(items)
        session.add_all(tasks)
        session.commit()

        counts = {
            "product": session.query(Product).count(),
            "merchant_order": session.query(MerchantOrder).count(),
            "order_item": session.query(OrderItem).count(),
            "task": session.query(Task).count(),
        }
        for table, count in counts.items():
            print(f"seed: {table} 插入 {count} 行")


if __name__ == "__main__":
    seed()
