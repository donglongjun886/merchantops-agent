"""getTask 工具：查询经营任务及最新进度（task + task_progress）。

两种用法：
- 传 merchantId：返回该商家全部任务（含最新进度），运营问"完成度"时 LLM 用这个
- 传 taskId：返回单个任务（含最新进度）
"""

import json

from sqlalchemy import select

from ..agent.tool import Tool, ToolArgumentError
from .parse import parse_arguments
from app.db.models import Task, TaskProgress
from app.db.session import SessionLocal


def _to_int(raw, field_name: str) -> int | None:
    """容错转 int：非数字返回 None 并给出 message。"""
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _latest_progress(session, task_id: int) -> TaskProgress | None:
    return session.execute(
        select(TaskProgress)
        .where(TaskProgress.task_id == task_id)
        .order_by(TaskProgress.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def _task_dict(task: Task, progress: TaskProgress | None) -> dict:
    return {
        "taskId": task.id,
        "merchantId": task.merchant_id,
        "name": task.name,
        "metricType": task.metric_type,
        "targetValue": float(task.target_value),
        "currentValue": float(progress.current_value) if progress else None,
        "progress": float(progress.progress) if progress else None,
        "status": task.status,
    }


class GetTaskTool(Tool):
    @property
    def name(self) -> str:
        return "getTask"

    @property
    def description(self) -> str:
        return (
            "查询经营任务：按商家ID返回其全部任务及最新进度（目标值/当前值/完成百分比），"
            "或按任务ID查询单个任务。两个参数至少给一个。"
        )

    @property
    def parameters_json(self) -> str:
        return json.dumps(
            {
                "type": "object",
                "properties": {
                    "merchantId": {
                        "type": "integer",
                        "description": "商家ID（数字），按商家查询其全部任务",
                    },
                    "taskId": {"type": "integer", "description": "任务ID（数字），查询单个任务"},
                },
            }
        )

    def execute(self, arguments_json: str) -> str:
        args = parse_arguments(arguments_json)
        merchant_id = _to_int(args.get("merchantId"), "merchantId")
        task_id = _to_int(args.get("taskId"), "taskId")

        if args.get("merchantId") is not None and merchant_id is None:
            return json.dumps({"found": False, "message": "商家ID必须是数字"}, ensure_ascii=False)
        if args.get("taskId") is not None and task_id is None:
            return json.dumps({"found": False, "message": "任务ID必须是数字"}, ensure_ascii=False)
        if merchant_id is None and task_id is None:
            raise ToolArgumentError("请提供参数 taskId 或 merchantId")

        with SessionLocal() as session:
            if merchant_id is not None:
                tasks = session.execute(
                    select(Task).where(Task.merchant_id == merchant_id).order_by(Task.id)
                ).scalars().all()
                if not tasks:
                    return json.dumps(
                        {"found": False, "message": f"商家 id={merchant_id} 没有经营任务"},
                        ensure_ascii=False,
                    )
                return json.dumps(
                    {
                        "merchantId": merchant_id,
                        "tasks": [_task_dict(t, _latest_progress(session, t.id)) for t in tasks],
                    },
                    ensure_ascii=False,
                )

            task = session.execute(
                select(Task).where(Task.id == task_id)
            ).scalar_one_or_none()
            if task is None:
                return json.dumps({"found": False, "message": f"未找到任务 id={task_id}"}, ensure_ascii=False)
            return json.dumps(_task_dict(task, _latest_progress(session, task.id)), ensure_ascii=False)
