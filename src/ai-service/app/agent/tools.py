"""业务工具：Agent 通过受控内部接口访问 Spring Boot 业务能力。

只暴露查询与"建单前校验"，写操作必须由用户在页面上确认后由后端执行。
"""
from __future__ import annotations

import json
import logging

import requests

from app.config import settings

log = logging.getLogger("labcare.agent")


class ToolError(RuntimeError):
    pass


class BusinessTools:
    def __init__(self) -> None:
        self._base = settings.backend_base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-Internal-Token": settings.internal_token,
                "Content-Type": "application/json",
            }
        )

    def _get(self, path: str, params: dict | None = None) -> dict:
        try:
            response = self._session.get(self._base + path, params=params, timeout=settings.backend_timeout)
        except requests.RequestException as exc:
            raise ToolError(f"业务接口不可用：{exc}") from exc
        return self._unwrap(response)

    def _post(self, path: str, payload: dict) -> dict:
        try:
            response = self._session.post(self._base + path, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          timeout=settings.backend_timeout)
        except requests.RequestException as exc:
            raise ToolError(f"业务接口不可用：{exc}") from exc
        return self._unwrap(response)

    @staticmethod
    def _unwrap(response: requests.Response) -> dict:
        try:
            body = response.json()
        except ValueError:
            raise ToolError(f"业务接口返回非 JSON（HTTP {response.status_code}）")
        if response.status_code >= 400 or body.get("code") != 0:
            raise ToolError(body.get("message") or f"业务接口错误（HTTP {response.status_code}）")
        return body.get("data") or {}

    # ------------------------------------------------------------------
    def search_equipment(self, keyword: str = "") -> list[dict]:
        data = self._get("/internal/tools/equipments", {"keyword": keyword or ""})
        return data if isinstance(data, list) else []

    def get_equipment(self, equipment_id: int) -> dict:
        return self._get(f"/internal/tools/equipments/{int(equipment_id)}")

    def prepare_repair(self, equipment_id: int, description: str, contact: str = "") -> dict:
        return self._post(
            "/internal/tools/repairs/prepare",
            {"equipmentId": int(equipment_id), "description": description, "contact": contact},
        )


TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "search_equipment",
            "description": "按关键词查询实验室设备台账，返回设备 id、编号、名称、实验室与状态。关键词可以是设备名称、类别或编号。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "设备名称/类别/编号关键词，可为空表示列出全部"}
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_equipment",
            "description": "按设备 id 查询设备详情，包含位置、状态、简介与使用说明。",
            "parameters": {
                "type": "object",
                "properties": {"equipment_id": {"type": "integer", "description": "设备 id"}},
                "required": ["equipment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_repair",
            "description": "准备一张报修工单（只生成预览，不会真正提交）。需要设备 id 与故障描述；返回内容用于让用户确认。",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipment_id": {"type": "integer", "description": "设备 id"},
                    "description": {"type": "string", "description": "故障现象描述"},
                    "contact": {"type": "string", "description": "联系方式，可为空"},
                },
                "required": ["equipment_id", "description"],
            },
        },
    },
]


def dispatch(name: str, args: dict, tools: BusinessTools) -> dict:
    if name == "search_equipment":
        return {"items": tools.search_equipment(str(args.get("keyword", "")))}
    if name == "get_equipment":
        return tools.get_equipment(int(args.get("equipment_id")))
    if name == "prepare_repair":
        return tools.prepare_repair(
            int(args.get("equipment_id")),
            str(args.get("description", "")),
            str(args.get("contact", "")),
        )
    raise ToolError(f"未知工具：{name}")
