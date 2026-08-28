"""getMerchant 工具：查询真库 merchant 表，按商家ID返回名称、状态、创建时间。"""

import json

from ..agent.tool import Tool, ToolArgumentError
from .parse import parse_arguments


class GetMerchantTool(Tool):
    @property
    def name(self) -> str:
        return "getMerchant"

    @property
    def description(self) -> str:
        return "根据商家ID查询商家信息（名称、状态、创建时间）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {
                    "merchantId": {"type": "integer", "description": "商家ID（数字）"}
                },
                "required": ["merchantId"],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = parse_arguments(arguments_json)
        raw = args.get("merchantId")
        if raw is None:
            raise ToolArgumentError("缺少必填参数 merchantId")
        try:
            merchant_id = int(raw)
        except (TypeError, ValueError):
            return json.dumps({"found": False, "message": "商家ID必须是数字"}, ensure_ascii=False)

        from app.db.session import SessionLocal
        from app.db.models import Merchant
        from sqlalchemy import select

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
