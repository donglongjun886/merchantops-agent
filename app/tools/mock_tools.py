"""Mock 工具：查询商户 / 任务信息（演示用，返回固定数据）。"""

import json

from ..agent.tool import Tool, ToolArgumentError


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
        args = self._parse_arguments(arguments_json)
        merchant_id = args.get("merchantId")
        if not merchant_id:
            raise ToolArgumentError("缺少必填参数 merchantId")
        return json.dumps(
            {
                "merchantId": merchant_id,
                "name": f"测试商户-{merchant_id}",
                "status": "ACTIVE",
                "level": "金牌",
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_arguments(arguments_json: str) -> dict:
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as exc:
            raise ToolArgumentError(f"参数不是合法 JSON: {exc}") from exc
        if not isinstance(args, dict):
            raise ToolArgumentError(f"参数应为 JSON 对象，实际为 {type(args).__name__}")
        return args


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
        args = self._parse_arguments(arguments_json)
        task_id = args.get("taskId")
        if not task_id:
            raise ToolArgumentError("缺少必填参数 taskId")
        return json.dumps(
            {
                "taskId": task_id,
                "title": "处理商户入驻审核",
                "status": "IN_PROGRESS",
                "owner": "运营-小林",
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_arguments(arguments_json: str) -> dict:
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as exc:
            raise ToolArgumentError(f"参数不是合法 JSON: {exc}") from exc
        if not isinstance(args, dict):
            raise ToolArgumentError(f"参数应为 JSON 对象，实际为 {type(args).__name__}")
        return args
