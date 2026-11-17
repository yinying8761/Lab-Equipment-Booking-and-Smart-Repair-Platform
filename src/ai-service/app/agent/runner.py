"""Agent 编排：工具调用循环 + 无模型时的确定性降级编排。

两条路径都不直接写业务数据：prepare_repair 只返回预览，
真正建单由用户在界面确认后由 Spring Boot 后端执行。
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.tools import TOOL_SPECS, BusinessTools, ToolError, dispatch
from app.config import settings
from app.llm import get_llm

log = logging.getLogger("labcare.agent")

AGENT_PROMPT = """你是「实验室设备预约与智能报修平台」的智能助手，负责帮用户查设备、准备报修单。
必须遵守：
1. 查询设备必须调用工具（search_equipment / get_equipment），不得编造设备编号、状态或位置。
2. 用户要报修时，先确认是哪台设备与故障现象，再调用 prepare_repair 生成预览。
3. prepare_repair 只是"准备"，工单尚未创建。必须明确告诉用户需要点击确认后才会提交，
   严禁宣称"已经创建/已提交/工单号是……"。
4. 信息不足时主动追问：设备是哪一台、具体故障现象、联系方式。
5. 回答用中文，简洁、分点，不输出工具调用细节。"""

REPAIR_HINTS = ["报修", "故障", "坏了", "不工作", "无法", "不能", "异常", "异响", "报错", "失灵",
                "破损", "漏水", "报警", "维修", "修一下", "打不开", "没反应"]

_CODE_PATTERN = re.compile(r"EQ[-\s]?\d{2,4}", re.IGNORECASE)


def _history_messages(history: list[dict]) -> list:
    messages = []
    for item in history:
        role = item.get("role", "user")
        content = item.get("content", "")
        if not content:
            continue
        messages.append(AIMessage(content=content) if role == "assistant" else HumanMessage(content=content))
    return messages


def _proposal_from(data: dict) -> dict:
    return {
        "actionType": "CREATE_REPAIR",
        "equipmentId": int(data.get("equipmentId") or 0),
        "equipmentCode": data.get("equipmentCode", ""),
        "equipmentName": data.get("equipmentName", ""),
        "description": data.get("description", ""),
        "contact": data.get("contact", ""),
        "preview": data.get("preview", ""),
    }


def _brief(items: list[dict], limit: int = 4) -> str:
    lines = []
    for item in items[:limit]:
        lines.append(f"{item.get('code')} {item.get('name')}（{item.get('laboratory')}，{item.get('statusLabel')}）")
    return "；".join(lines) if lines else "没有匹配的设备"


def run(message: str, history: list[dict] | None = None, user: dict | None = None) -> dict:
    history = history or []
    tools = BusinessTools()
    llm = get_llm()
    if llm is None:
        return _degraded_run(message, tools, user or {})
    try:
        return _llm_run(message, history, tools, user or {})
    except Exception as exc:
        log.exception("Agent 执行失败，降级为规则编排")
        result = _degraded_run(message, tools, user or {})
        result["notice"] = f"模型调用失败（{type(exc).__name__}），已降级为规则化工具编排"
        result["degraded"] = True
        return result


# ----------------------------------------------------------------------
# 有大模型：标准 tool-calling 循环
# ----------------------------------------------------------------------
def _llm_run(message: str, history: list[dict], tools: BusinessTools, user: dict) -> dict:
    llm = get_llm()
    model = llm.bind_tools(TOOL_SPECS)
    messages = [SystemMessage(content=AGENT_PROMPT)]
    messages.extend(_history_messages(history))
    messages.append(HumanMessage(content=message))

    trace: list[dict] = []
    proposal = None
    step = 0

    for _ in range(4):
        response = model.invoke(messages)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            text = _content_to_text(response.content)
            if proposal and "确认" not in text:
                text += "\n\n（报修单尚未提交，请在下方确认卡片中点击「确认提交」后才会真正创建。）"
            return {
                "reply": text.strip() or "智能助手没有生成有效回复，请换个说法再试。",
                "trace": trace,
                "proposal": proposal,
                "degraded": False,
                "notice": "",
                "meta": {"mode": "llm", "model": settings.llm_model},
            }
        messages.append(response)
        for call in tool_calls:
            step += 1
            name = call.get("name", "")
            args = call.get("args", {}) or {}
            try:
                data = dispatch(name, args, tools)
                summary = _summarise(name, data)
                trace.append({"step": step, "tool": name, "input": _short(json.dumps(args, ensure_ascii=False)),
                              "output": _short(summary), "success": True})
                if name == "prepare_repair":
                    proposal = _proposal_from(data)
                messages.append(ToolMessage(content=json.dumps(data, ensure_ascii=False),
                                            tool_call_id=call.get("id", "")))
            except (ToolError, ValueError, TypeError) as exc:
                trace.append({"step": step, "tool": name, "input": _short(json.dumps(args, ensure_ascii=False)),
                              "output": _short(str(exc)), "success": False})
                messages.append(ToolMessage(content=json.dumps({"error": str(exc)}, ensure_ascii=False),
                                            tool_call_id=call.get("id", "")))

    return {
        "reply": "工具调用次数过多，请把问题拆成更具体的描述后重试（例如指定设备编号与故障现象）。",
        "trace": trace,
        "proposal": proposal,
        "degraded": False,
        "notice": "达到最大工具调用轮次",
        "meta": {"mode": "llm", "model": settings.llm_model},
    }


def _summarise(name: str, data) -> str:
    if name == "search_equipment":
        items = data.get("items", []) if isinstance(data, dict) else []
        return f"命中 {len(items)} 台设备：" + _brief(items)
    if name == "get_equipment":
        return f"{data.get('code')} {data.get('name')}（{data.get('laboratory')}，{data.get('statusLabel')}）"
    if name == "prepare_repair":
        return "已生成待确认报修预览：" + str(data.get("preview", ""))
    return str(data)


# ----------------------------------------------------------------------
# 无大模型：确定性规则编排（仍然真实调用业务工具）
# ----------------------------------------------------------------------
def _degraded_run(message: str, tools: BusinessTools, user: dict) -> dict:
    trace: list[dict] = []
    step = 0
    try:
        keyword = ""
        match = _CODE_PATTERN.search(message)
        if match:
            keyword = match.group(0).upper().replace(" ", "-")
        step += 1
        items = tools.search_equipment(keyword)
        trace.append({
            "step": step, "tool": "search_equipment",
            "input": _short(keyword or "（全部设备）"),
            "output": _short(f"命中 {len(items)} 台设备：" + _brief(items)),
            "success": True,
        })
    except ToolError as exc:
        return {
            "reply": f"业务系统暂时不可用（{exc}）。你仍然可以在「报修」页面手动提交工单。",
            "trace": trace, "proposal": None, "degraded": True,
            "notice": "数据查询失败，未生成任何推测结果", "meta": {"mode": "rule"},
        }

    chosen = _match_equipment(message, items)
    wants_repair = any(hint in message for hint in REPAIR_HINTS)

    if wants_repair:
        if chosen is None:
            return {
                "reply": "可以帮你准备报修单，但需要先确认设备。请告诉我是哪一台设备，例如：\n"
                         + _brief(items, 5),
                "trace": trace, "proposal": None, "degraded": True,
                "notice": "当前为基础模式：检索与工具调用真实执行，自然语言理解能力有限",
                "meta": {"mode": "rule"},
            }
        description = _clean_description(message)
        if len(description) < 6:
            return {
                "reply": f"已确定设备为 {chosen.get('code')} {chosen.get('name')}。请再补充具体的故障现象，"
                         "例如「运行时异响」「温度无法上升」，我会生成报修预览供你确认。",
                "trace": trace, "proposal": None, "degraded": True,
                "notice": "当前为基础模式", "meta": {"mode": "rule"},
            }
        try:
            step += 1
            data = tools.prepare_repair(int(chosen["id"]), description, "")
            trace.append({
                "step": step, "tool": "prepare_repair",
                "input": _short(f"equipment_id={chosen['id']}, description={description}"),
                "output": _short(data.get("preview", "")), "success": True,
            })
            return {
                "reply": f"已为 {chosen.get('code')} {chosen.get('name')} 准备好报修内容：\n{description}\n\n"
                         "请点击下方「确认提交」后才会真正创建工单；取消则不会产生任何记录。",
                "trace": trace, "proposal": _proposal_from(data), "degraded": True,
                "notice": "当前为基础模式：检索与工具调用真实执行，自然语言理解能力有限",
                "meta": {"mode": "rule"},
            }
        except ToolError as exc:
            trace.append({"step": step, "tool": "prepare_repair", "input": "", "output": str(exc), "success": False})
            return {
                "reply": f"准备报修单失败：{exc}。你可以到「报修」页面手动提交，基础业务不受影响。",
                "trace": trace, "proposal": None, "degraded": True,
                "notice": "工具调用失败", "meta": {"mode": "rule"},
            }

    if chosen is not None:
        detail = chosen
        try:
            step += 1
            detail = tools.get_equipment(int(chosen["id"]))
            trace.append({
                "step": step, "tool": "get_equipment", "input": str(chosen["id"]),
                "output": _short(f"{detail.get('code')} {detail.get('name')} {detail.get('statusLabel')}"),
                "success": True,
            })
        except ToolError:
            pass
        return {
            "reply": f"{detail.get('code')} {detail.get('name')}\n"
                     f"类别：{detail.get('category', '-')}\n"
                     f"实验室：{detail.get('laboratory', '-')}（{detail.get('location', '-')}）\n"
                     f"状态：{detail.get('statusLabel', '-')}\n"
                     f"使用说明：{detail.get('usageNote', '-')}\n\n"
                     f"需要我帮你为这台设备准备一张报修单吗？",
            "trace": trace, "proposal": None, "degraded": True,
            "notice": "当前为基础模式", "meta": {"mode": "rule"},
        }

    return {
        "reply": "我可以帮你查设备或准备报修单。请提供设备编号（如 EQ-002）或设备名称，"
                 "如果是要报修，请说明故障现象。\n当前设备：" + _brief(items, 5),
        "trace": trace, "proposal": None, "degraded": True,
        "notice": "当前为基础模式", "meta": {"mode": "rule"},
    }


def _match_equipment(message: str, items: list[dict]) -> dict | None:
    if not items:
        return None
    text = message.lower()
    for item in items:
        code = str(item.get("code", "")).lower()
        if code and code in text:
            return item
    for item in items:
        name = str(item.get("name", ""))
        if len(name) >= 2 and name in message:
            return item
    if _CODE_PATTERN.search(message):
        return items[0]
    return None


def _clean_description(message: str) -> str:
    text = message.strip()
    for prefix in ("帮我报修", "我要报修", "报修", "麻烦", "请", "帮我", "一下"):
        text = text.replace(prefix, "")
    return text.strip("，。 ,.") or message.strip()


def _content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


def _short(text: str, limit: int = 300) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "…"
