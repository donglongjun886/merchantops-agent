"""getOrder 工具：查询订单（merchant_order + merchant）。

两种查询模式：
1. 按业务订单号单查：返回订单详情（订单号、商家名、金额、状态、创建时间）
2. 按商家ID / 状态过滤查订单列表：最多返回 50 条，按创建时间倒序
"""

import json

from sqlalchemy import select

from ..agent.tool import Tool, ToolArgumentError
from ..db.models import Merchant, MerchantOrder
from ..db.session import SessionLocal
from .parse import parse_arguments


class GetOrderTool(Tool):
    @property
    def name(self) -> str:
        return "getOrder"

    @property
    def description(self) -> str:
        return "查询订单：按订单号单查，或按商家ID/状态过滤查订单列表（如查风控审核中的订单）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {
                    "orderId": {"type": "string", "description": "业务订单号，单查"},
                    "merchantId": {"type": "integer", "description": "商家ID，查该商家全部订单"},
                    "status": {
                        "type": "string",
                        "description": "订单状态（PENDING/PAID/SHIPPED/COMPLETED/CANCELLED/REFUNDED/RISK_REVIEW），可单独用或与 merchantId 组合过滤",
                    },
                },
                "required": [],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = parse_arguments(arguments_json)
        order_id = args.get("orderId")
        merchant_id = args.get("merchantId")
        status = args.get("status")
        if order_id in (None, "") and merchant_id is None and status in (None, ""):
            raise ToolArgumentError("请提供参数 orderId、merchantId 或 status")
        with SessionLocal() as session:
            if order_id not in (None, ""):
                # 单查
                order = session.execute(
                    select(MerchantOrder).where(MerchantOrder.order_id == order_id)
                ).scalar_one_or_none()
                if order is None:
                    return json.dumps(
                        {"found": False, "message": f"未找到订单 order_id={order_id}"},
                        ensure_ascii=False,
                    )
                merchant = session.get(Merchant, order.merchant_id)
                return json.dumps(
                    {
                        "orderId": order.order_id,
                        "merchantName": merchant.name if merchant else None,
                        "amount": float(order.amount),
                        "status": order.status,
                        "createdAt": str(order.created_at),
                    },
                    ensure_ascii=False,
                )
            # 列表查询：按商家ID / 状态过滤
            conditions = []
            if merchant_id is not None:
                try:
                    merchant_id = int(merchant_id)
                except (TypeError, ValueError):
                    return json.dumps(
                        {"found": False, "message": "商家ID必须是数字"}, ensure_ascii=False
                    )
                conditions.append(MerchantOrder.merchant_id == merchant_id)
            if status not in (None, ""):
                conditions.append(MerchantOrder.status == status)
            rows = session.execute(
                select(MerchantOrder, Merchant.name)
                .join(Merchant, Merchant.id == MerchantOrder.merchant_id)
                .where(*conditions)
                .order_by(MerchantOrder.created_at.desc())
                .limit(50)
            ).all()
            if not rows:
                return json.dumps(
                    {"count": 0, "orders": [], "message": "没有符合条件的订单"},
                    ensure_ascii=False,
                )
            orders = [
                {
                    "orderId": order.order_id,
                    "merchantName": merchant_name,
                    "amount": float(order.amount),
                    "status": order.status,
                    "createdAt": str(order.created_at),
                }
                for order, merchant_name in rows
            ]
            return json.dumps({"count": len(orders), "orders": orders}, ensure_ascii=False)
