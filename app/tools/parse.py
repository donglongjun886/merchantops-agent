"""工具参数解析公共函数（各工具共用，避免重复代码）。"""

import json

from ..agent.tool import ToolArgumentError


def parse_arguments(arguments_json: str) -> dict:
    try:
        args = json.loads(arguments_json)
    except json.JSONDecodeError as exc:
        raise ToolArgumentError(f"参数不是合法 JSON: {exc}") from exc
    if not isinstance(args, dict):
        raise ToolArgumentError(f"参数应为 JSON 对象，实际为 {type(args).__name__}")
    return args
