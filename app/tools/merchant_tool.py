"""getMerchant 工具：查询真库 merchant 表。

两种查询模式：
- 传 merchantId：按商家ID精确查，返回单个商家的名称、状态、创建时间
- 传 name：按名称模糊查（如"星辰"匹配"星辰数码旗舰店"），返回匹配的商家列表
"""

import json

from sqlalchemy import select

from ..agent.tool import Tool, ToolArgumentError
from .parse import parse_arguments
from app.db.models import Merchant
from app.db.session import SessionLocal


class GetMerchantTool(Tool):
    @property
    def name(self) -> str:
        return "getMerchant"

    @property
    def description(self) -> str:
        return "查询商家：按商家ID精确查，或按名称模糊查（返回匹配的商家列表）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {
                    "merchantId": {
                        "type": "integer",
                        "description": "商家ID（数字），精确查单个商家",
                    },
                    "name": {
                        "type": "string",
                        "description": "商家名称，支持模糊匹配（如\"星辰\"匹配\"星辰数码旗舰店\"）",
                    },
                },
                "required": [],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = parse_arguments(arguments_json)
        raw_id = args.get("merchantId")
        name = args.get("name")

        if raw_id is None and not name:
            raise ToolArgumentError("请提供参数 merchantId 或 name")

        if raw_id is not None:
            try:
                merchant_id = int(raw_id)
            except (TypeError, ValueError):
                return json.dumps({"found": False, "message": "商家ID必须是数字"}, ensure_ascii=False)

            with SessionLocal() as session:
                merchant = session.execute(
                    select(Merchant).where(Merchant.id == merchant_id)
                ).scalar_one_or_none()

            if merchant is None:
                return json.dumps({"found": False, "message": f"未找到商家 id={merchant_id}"}, ensure_ascii=False)

            return json.dumps(
                {
                    "merchantId": merchant.id,
                    "name": merchant.name,
                    "status": merchant.status,
                    "createdAt": str(merchant.created_at),
                },
                ensure_ascii=False,
            )

        with SessionLocal() as session:
            merchants = session.execute(
                select(Merchant)
                .where(Merchant.name.like(f"%{name}%"))
                .order_by(Merchant.id)
                .limit(10)
            ).scalars().all()

        if not merchants:
            return json.dumps({"found": False, "message": f"未找到名称包含 {name} 的商家"}, ensure_ascii=False)

        return json.dumps(
            {
                "matches": [
                    {"merchantId": m.id, "name": m.name, "status": m.status}
                    for m in merchants
                ]
            },
            ensure_ascii=False,
        )
