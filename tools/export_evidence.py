"""导出验收证据：RAG 检索验证与 Agent 执行轨迹。

用法：python tools/export_evidence.py（需后端 8080 与 AI 服务 8100 已启动）
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8080/api"
RAG_DIR = ROOT / "evidence" / "RAG检索验证"
AGENT_DIR = ROOT / "evidence" / "Agent执行轨迹"

RAG_QUESTIONS = [
    ("命中手册", "离心机报 E07 怎么处理？"),
    ("跨文档检索", "生物安全柜使用前需要做什么？"),
    ("证据不足", "食堂今天中午有什么菜？"),
]

AGENT_MESSAGES = [
    ("查询设备", "查一下 EQ-001 的使用说明"),
    ("准备报修", "EQ-002 电镜真空度上不去，帮我报修"),
]


def call(method: str, path: str, token: str | None = None, body=None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.request(method, f"{BASE}{path}", headers=headers, json=body, timeout=120)
    return response.json()


def main() -> None:
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    AGENT_DIR.mkdir(parents=True, exist_ok=True)

    token = call("POST", "/auth/login", body={"username": "student01", "password": "Student@123"})["data"]["token"]

    # ---------------- RAG ----------------
    rag_records = []
    sessions = []
    for label, question in RAG_QUESTIONS:
        data = call("POST", "/ai/chat", token, {"question": question})["data"]
        sessions.append(data.get("sessionId"))
        rag_records.append({
            "label": label,
            "question": question,
            "sessionId": data.get("sessionId"),
            "answer": data.get("answer"),
            "degraded": data.get("degraded"),
            "notice": data.get("notice"),
            "citations": data.get("citations"),
        })

    (RAG_DIR / "rag_queries.json").write_text(
        json.dumps({"generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "records": rag_records},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# RAG 检索验证记录", "", f"导出时间：{datetime.now():%Y-%m-%d %H:%M:%S}", ""]
    for record in rag_records:
        lines.append(f"## {record['label']}：{record['question']}")
        lines.append("")
        lines.append(f"- 会话 id：{record['sessionId']}")
        lines.append(f"- 是否降级：{'是（未配置模型 Key，回答为检索摘要）' if record['degraded'] else '否'}")
        if record["notice"]:
            lines.append(f"- 提示：{record['notice']}")
        lines.append("")
        lines.append("**回答**")
        lines.append("")
        lines.append("```text")
        lines.append(record["answer"] or "")
        lines.append("```")
        lines.append("")
        if record["citations"]:
            lines.append("**引用来源**")
            lines.append("")
            lines.append("| 序号 | 文档 | 片段 | 相关度 | 摘要 |")
            lines.append("| --- | --- | --- | --- | --- |")
            for index, citation in enumerate(record["citations"], start=1):
                snippet = (citation.get("snippet") or "").replace("|", "／").replace("\n", " ")[:80]
                lines.append(f"| {index} | {citation.get('title')} | 第 {citation.get('chunkIndex') + 1} 段 | "
                             f"{citation.get('score'):.3f} | {snippet} |")
        else:
            lines.append("**引用来源**：无（判定为证据不足，未生成推测性结论）")
        lines.append("")
    (RAG_DIR / "rag_verification.md").write_text("\n".join(lines), encoding="utf-8")

    # ---------------- Agent ----------------
    agent_records = []
    for label, message in AGENT_MESSAGES:
        data = call("POST", "/ai/agent/chat", token, {"message": message})["data"]
        trace = call("GET", f"/ai/sessions/{data['sessionId']}/trace", token)["data"]
        agent_records.append({
            "label": label,
            "message": message,
            "sessionId": data["sessionId"],
            "reply": data.get("answer"),
            "degraded": data.get("degraded"),
            "trace": trace,
            "proposal": data.get("confirm"),
        })

    (AGENT_DIR / "agent_trace.json").write_text(
        json.dumps({"generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "records": agent_records},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# Agent 执行轨迹记录", "", f"导出时间：{datetime.now():%Y-%m-%d %H:%M:%S}", "",
             "每条记录对应一次对话：用户输入 → 工具调用（入参/返回）→ 回复或待确认提案。", ""]
    for record in agent_records:
        lines.append(f"## {record['label']}：{record['message']}")
        lines.append("")
        lines.append(f"- 会话 id：{record['sessionId']}")
        lines.append(f"- 是否降级：{'是（规则化工具编排）' if record['degraded'] else '否（大模型 tool-calling）'}")
        lines.append("")
        lines.append("| 步骤 | 工具 | 入参 | 返回 | 成功 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for step in record["trace"]:
            lines.append(f"| {step['step']} | {step['tool']} | {str(step['input'])[:60]} | "
                         f"{str(step['output'])[:80]} | {'是' if step['success'] else '否'} |")
        lines.append("")
        lines.append("**助手回复**")
        lines.append("")
        lines.append("```text")
        lines.append(record["reply"] or "")
        lines.append("```")
        lines.append("")
        if record["proposal"]:
            lines.append("**待确认提案（未写入数据库）**")
            lines.append("")
            lines.append(f"- 设备：{record['proposal']['equipmentCode']} {record['proposal']['equipmentName']}")
            lines.append(f"- 故障描述：{record['proposal']['description']}")
            lines.append(f"- 预览：{record['proposal']['preview']}")
            lines.append(f"- 令牌过期时间：{record['proposal']['expiresAt']}")
            lines.append("")
    (AGENT_DIR / "agent_trace.md").write_text("\n".join(lines), encoding="utf-8")

    print("已导出：")
    print(" ", RAG_DIR / "rag_verification.md")
    print(" ", RAG_DIR / "rag_queries.json")
    print(" ", AGENT_DIR / "agent_trace.md")
    print(" ", AGENT_DIR / "agent_trace.json")


if __name__ == "__main__":
    main()
