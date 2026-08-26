"""Mock 工具：查询商户 / 任务信息（演示用，返回固定数据）。"""

import json

from ..agent.tool import Tool


class GetMerchantTool(Tool):
    @property
    def name(self) -> str:
        return "getMerchant"

    @property
    def description(self) -> str:
        return "根据商户ID查询商户信息（名称、状态、等级）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {"merchantId": {"type": "string", "description": "商户ID"}},
                "required": ["merchantId"],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = json.loads(arguments_json)
        merchant_id = args.get("merchantId", "")
        return json.dumps(
            {
                "merchantId": merchant_id,
                "name": f"测试商户-{merchant_id}",
                "status": "ACTIVE",
                "level": "金牌",
            },
            ensure_ascii=False,
        )


class GetTaskTool(Tool):
    @property
    def name(self) -> str:
        return "getTask"

    @property
    def description(self) -> str:
        return "根据任务ID查询任务信息（标题、状态、负责人）"

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {"taskId": {"type": "string", "description": "任务ID"}},
                "required": ["taskId"],
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = json.loads(arguments_json)
        task_id = args.get("taskId", "")
        return json.dumps(
            {
                "taskId": task_id,
                "title": "处理商户入驻审核",
                "status": "IN_PROGRESS",
                "owner": "运营-小林",
            },
            ensure_ascii=False,
        )
