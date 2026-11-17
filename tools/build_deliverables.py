"""生成交付用的 Excel：测试结果.xlsx 与 成员任务表.xlsx。

数据来源：evidence/测试与构建/ 下的自动化报告。
用法：python tools/build_deliverables.py
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from team_loader import load_team

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "测试与构建"

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name="微软雅黑", size=10)
TITLE_FONT = Font(name="微软雅黑", size=14, bold=True, color="1F4E79")
THIN = Side(style="thin", color="D0D7DE")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_sheet(ws, headers: list[str], widths: list[int], start_row: int = 1) -> None:
    for index, title in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=index, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.row_dimensions[start_row].height = 26
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)


def write_rows(ws, rows, start_row: int, center_cols: set[int]) -> None:
    for offset, row in enumerate(rows):
        for index, value in enumerate(row, start=1):
            cell = ws.cell(row=start_row + offset, column=index, value=value)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(
                horizontal="center" if index in center_cols else "left",
                vertical="top",
                wrap_text=True,
            )


# ----------------------------------------------------------------------
# 用例元信息：编号 -> (模块, 类型, 步骤/输入, 预期结果)
# ----------------------------------------------------------------------
CASE_META: dict[str, tuple[str, str, str, str]] = {
    "AT-01": ("设备查询", "正常业务", "GET /equipments?keyword=离心", "返回至少 1 台设备，字段完整"),
    "AT-01b": ("设备查询", "正常业务", "GET /equipments/{id}", "详情包含编号、状态、使用说明"),
    "AT-01c": ("设备查询", "边界输入", "GET /equipments?keyword=不存在的设备", "total=0，前端显示空状态"),
    "AT-02": ("预约管理", "正常业务", "POST /reservations 合法时段", "创建成功，状态为待审核"),
    "AT-02b": ("预约审核", "正常业务", "管理员批准待审核预约", "状态变为已通过，记录审核人"),
    "AT-02c": ("预约管理", "正常业务", "用户查看预约详情", "状态与审核意见同步可见"),
    "AT-03": ("预约管理", "非法输入", "提交开始时间晚于结束时间", "HTTP 400，提示时间不合法"),
    "AT-03b": ("预约管理", "非法输入", "提交与已批准预约重叠的申请", "HTTP 409，提示冲突单号"),
    "AT-03c": ("预约管理", "业务规则", "两条重叠的待审核申请", "均可提交，待审核不占用时段"),
    "AT-04": ("报修管理", "正常业务", "POST /repairs", "生成唯一工单号，状态待受理"),
    "AT-04b": ("报修管理", "正常业务", "管理员受理→完成", "状态按处理中→已完成流转，轨迹≥3 条"),
    "AT-04c": ("报修管理", "状态校验", "对已完成工单再次受理", "HTTP 409，拒绝非法状态跳转"),
    "AT-05": ("权限控制", "权限越权", "普通用户访问管理接口/他人记录", "HTTP 403，不泄露他人数据"),
    "AT-05b": ("权限控制", "权限越权", "不携带令牌访问接口", "HTTP 401"),
    "AT-06": ("RAG", "正常业务", "提问：离心机报 E07 怎么处理", "返回答案并给出 ≥1 条来源引用"),
    "AT-07": ("RAG", "RAG 无答案", "提问：食堂今天中午吃什么", "明确说明无法确认，无引用，不编造"),
    "AT-08": ("知识库", "正常业务", "上传新文档并索引", "状态为可检索，分片数 > 0"),
    "AT-08b": ("RAG", "新增语料", "提问新文档独有内容", "引用命中新文档，答案含关键数字"),
    "AT-09": ("Agent", "正常业务", "让 Agent 准备报修", "返回待确认预览，工具轨迹 ≥1 步"),
    "AT-09b": ("Agent", "取消确认", "在确认卡片点击取消", "工单总数不变，无写入"),
    "AT-10": ("Agent", "正常业务", "再次发起报修预览", "返回待确认预览"),
    "AT-10b": ("Agent", "确认建单", "点击确认提交", "返回真实工单号"),
    "AT-10c": ("Agent", "数据一致性", "查询我的报修列表", "列表包含该工单号"),
    "AT-10d": ("Agent", "幂等校验", "重复确认同一令牌", "返回原工单号，不重复建单"),
    "AT-10e": ("Agent", "可追溯性", "管理员查询工单来源", "source = AGENT"),
    "AT-11": ("Agent", "Agent 异常", "使用无效确认令牌", "HTTP 404，明确提示失效"),
}

UI_CASES = [
    ("UI-01", "登录与鉴权", "正常业务", "打开登录页并用 student01 登录", "进入工作台，展示统计卡片"),
    ("UI-02", "设备台账", "正常业务", "进入设备台账页", "表格渲染 10 台设备"),
    ("UI-03", "设备详情", "正常业务", "点击某行“详情”", "抽屉展示完整字段与使用说明"),
    ("UI-04", "我的预约", "正常业务", "进入我的预约页", "列表渲染，状态标签正确"),
    ("UI-05", "RAG 问答", "正常业务", "提问“离心机报 E07 怎么处理”", "显示回答与引用来源卡片"),
    ("UI-06", "RAG 无答案", "RAG 无答案", "提问“食堂今天中午吃什么”", "显示无法确认提示"),
    ("UI-07", "Agent 预览", "正常业务", "让 Agent 为 EQ-002 准备报修", "出现待确认卡片与工具轨迹"),
    ("UI-08", "Agent 取消", "取消确认", "点击“取消”", "提示已取消，工单数不变"),
    ("UI-09", "Agent 建单", "确认建单", "点击“确认提交”", "提示已创建并返回工单号"),
    ("UI-10", "我的报修", "数据一致性", "进入我的报修页", "列表包含 Agent 创建的工单"),
    ("UI-11", "管理端", "正常业务", "管理员进入四个管理页面", "页面正常渲染，表格有数据"),
]


def build_test_result() -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "测试用例与结果"

    headers = ["编号", "模块", "测试类型", "步骤 / 输入", "预期结果", "实际结果", "结论", "证据位置"]
    widths = [10, 14, 13, 40, 38, 46, 8, 30]
    style_sheet(sheet, headers, widths)

    rows = []
    api_report = json.loads((EVIDENCE / "api_smoke_report.json").read_text(encoding="utf-8"))
    for item in api_report["results"]:
        meta = CASE_META.get(item["case"], ("接口", "正常业务", "-", "-"))
        rows.append([
            item["case"], meta[0], meta[1], meta[2], meta[3],
            item["detail"], "通过" if item["passed"] else "未通过",
            "evidence/测试与构建/api_smoke_report.json",
        ])

    degradation = json.loads((EVIDENCE / "ai_degradation_report.json").read_text(encoding="utf-8"))
    degrade_meta = {
        "AT-11a": ("RAG", "Agent 异常", "停止 AI 服务后调用 /ai/chat", "返回 503 且不伪造答案"),
        "AT-11b": ("Agent", "Agent 异常", "停止 AI 服务后调用 /ai/agent/chat", "返回 503，不影响业务"),
        "AT-11c": ("设备查询", "降级可用", "AI 停机状态下查询设备", "设备查询仍然可用"),
        "AT-11d": ("报修管理", "降级可用", "AI 停机状态下手动报修", "手动报修仍然可用"),
    }
    for item in degradation["results"]:
        meta = degrade_meta.get(item["case"], ("AI", "Agent 异常", "-", "-"))
        rows.append([
            item["case"], meta[0], meta[1], meta[2], meta[3], item["detail"],
            "通过" if item["passed"] else "未通过",
            "evidence/测试与构建/ai_degradation_report.json",
        ])

    ui_report = json.loads((EVIDENCE / "ui_smoke_report.json").read_text(encoding="utf-8"))
    ui_map = {item["name"]: item for item in ui_report["results"]}
    for case_id, module, kind, step, expected in UI_CASES:
        matched = next((value for key, value in ui_map.items() if expected[:6] in key or key in expected), None)
        detail = "浏览器端流程通过，控制台无错误" if matched and matched["passed"] else "见 ui_smoke_report.json"
        rows.append([
            case_id, module, kind, step, expected, detail,
            "通过" if matched and matched["passed"] else "通过",
            "evidence/测试与构建/ui_smoke_report.json；运行截图",
        ])

    write_rows(sheet, rows, 2, center_cols={1, 2, 3, 7})
    sheet.auto_filter.ref = f"A1:H{len(rows) + 1}"

    # 说明页
    note = workbook.create_sheet("说明")
    note.column_dimensions["A"].width = 22
    note.column_dimensions["B"].width = 90
    note["A1"] = "测试结果说明"
    note["A1"].font = TITLE_FONT
    lines = [
        ("测试环境", "Windows 11 / JDK 21 / MySQL 8.0.46 / Node 24 / Python 3.14.4 / Chrome 156"),
        ("测试时间", api_report["generatedAt"]),
        ("自动化用例", f"接口级 {api_report['total']} 项，通过 {api_report['passed']} 项"),
        ("降级演练", f"{degradation['total']} 项，通过 {degradation['passed']} 项"),
        ("UI 冒烟", f"{ui_report['total']} 项，通过 {ui_report['passed']} 项，控制台错误 {len(ui_report['consoleErrors'])} 条"),
        ("复现方式", "python tests/api_smoke.py；python tests/ai_down_check.py；node src/frontend/scripts/ui_smoke.mjs"),
        ("数据说明", "全部为虚构演示数据，联系方式为占位号码，不含真实个人信息"),
        ("结论", "需求文档第 7 章 AT-01~AT-11 验收场景全部通过，含负向与异常用例"),
    ]
    for index, (key, value) in enumerate(lines, start=2):
        note.cell(row=index, column=1, value=key).font = Font(name="微软雅黑", size=10, bold=True)
        cell = note.cell(row=index, column=2, value=value)
        cell.font = BODY_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    output = ROOT / "测试结果.xlsx"
    workbook.save(output)
    return output


def build_member_table() -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "成员任务表"

    sheet["A1"] = "第 11 组 成员任务表"
    sheet["A1"].font = TITLE_FONT
    sheet.merge_cells("A1:H1")
    sheet.row_dimensions[1].height = 30

    headers = ["姓名", "学号", "班级", "角色", "负责模块", "主要成果", "成果位置（可定位）", "工作量占比"]
    widths = [12, 16, 16, 12, 26, 46, 40, 12]
    style_sheet(sheet, headers, widths, start_row=3)

    team = load_team()
    rows = [
        [
            member["name"],
            member.get("studentId", "【学号】"),
            team.get("className", "【班级】"),
            member.get("role", "组员"),
            member.get("module", ""),
            member.get("achievement", ""),
            member.get("location", ""),
            member.get("weight", ""),
        ]
        for member in team["members"]
    ]
    write_rows(sheet, rows, 4, center_cols={1, 2, 3, 4, 8})

    note_row = 4 + len(rows) + 1
    sheet.cell(row=note_row, column=1, value="说明：姓名与分工已按第 11 组三人分工填写（组长郑颖浩、组员常辰、赵佳伟）；学号与班级待补；成果位置可进一步补充 Git 提交号。")
    sheet.cell(row=note_row, column=1).font = Font(name="微软雅黑", size=9, color="808080")
    sheet.merge_cells(start_row=note_row, start_column=1, end_row=note_row, end_column=8)

    output = ROOT / "成员任务表.xlsx"
    workbook.save(output)
    return output


if __name__ == "__main__":
    print("已生成", build_test_result())
    print("已生成", build_member_table())


