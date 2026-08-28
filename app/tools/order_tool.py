"""getOrder 工具：按业务订单号查询订单（merchant_order + merchant）。"""

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
        return "根据业务订单号查询订单信息（金额、状态、所属商家）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {"orderId": {"type": "string", "description": "业务订单号"}},
                "required": ["orderId"],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = parse_arguments(arguments_json)
        order_id = args.get("orderId")
        if order_id is None or order_id == "":
            raise ToolArgumentError("缺少必填参数 orderId")
        with SessionLocal() as session:
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
