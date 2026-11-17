"""读取 docs/team.json（成员与班级信息），供各交付物生成脚本共用。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_FILE = ROOT / "docs" / "team.json"

_FALLBACK = {
    "group": "第 11 组",
    "systemName": "实验室设备预约与智能报修平台",
    "className": "【班级】",
    "leader": "郑颖浩",
    "members": [
        {"name": "郑颖浩", "studentId": "【学号】", "role": "组长", "module": "后端底座、设备与预约主链路",
         "achievement": "11 张表与索引、JWT 鉴权与权限拦截、冲突控制与行锁、登录页与设备管理/预约审核页、部署联调",
         "location": "src/backend/**；db/init.sql；scripts/", "weight": "35%"},
        {"name": "常辰", "studentId": "【学号】", "role": "组员", "module": "报修工单、知识库与用户端页面",
         "achievement": "报修状态机与处理轨迹、知识库上传与索引重建、用户端与工单/知识库管理页",
         "location": "src/backend/**（repair、knowledge）；src/frontend/**", "weight": "33%"},
        {"name": "赵佳伟", "studentId": "【学号】", "role": "组员", "module": "RAG、Agent、智能助手与测试证据",
         "achievement": "RAG 管道与引用溯源、Agent 工具编排与确认提案、智能助手页面、自动化测试与证据",
         "location": "src/ai-service/app/**；tests/；evidence/", "weight": "32%"},
    ],
}


def load_team() -> dict:
    if TEAM_FILE.exists():
        try:
            return json.loads(TEAM_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return _FALLBACK


def member_names(team: dict) -> str:
    return "、".join(member["name"] for member in team.get("members", []))
