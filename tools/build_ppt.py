"""生成答辩 PPT：答辩PPT-实验室设备预约与智能报修平台.pptx

用法：python tools/build_ppt.py
"""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from team_loader import load_team, member_names

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "evidence" / "运行截图或录屏"
OUTPUT = ROOT / "答辩PPT-实验室设备预约与智能报修平台.pptx"

NAVY = RGBColor(0x1F, 0x4E, 0x79)
BLUE = RGBColor(0x2F, 0x6F, 0xB2)
LIGHT = RGBColor(0xEE, 0xF3, 0xF9)
GRAY = RGBColor(0x60, 0x6A, 0x76)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x26, 0x30, 0x3B)

FONT = "微软雅黑"


def style_text(text_frame, size=18, color=DARK, bold=False, align=PP_ALIGN.LEFT) -> None:
    for paragraph in text_frame.paragraphs:
        paragraph.alignment = align
        for run in paragraph.runs:
            run.font.name = FONT
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = color


def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_title_bar(slide, title: str, subtitle: str = "") -> None:
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs_width, Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    frame = bar.text_frame
    frame.margin_left = Inches(0.55)
    frame.margin_top = Inches(0.12)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = title
    run.font.name = FONT
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = WHITE
    if subtitle:
        chip = slide.shapes.add_textbox(prs_width - Inches(4.4), Inches(0.32), Inches(4.0), Inches(0.45))
        text_frame = chip.text_frame
        text_frame.text = subtitle
        style_text(text_frame, 12, RGBColor(0xC5, 0xD6, 0xE6), align=PP_ALIGN.RIGHT)


def add_bullets(slide, items, left=Inches(0.7), top=Inches(1.35), width=Inches(11.9),
                height=Inches(5.4), size=17) -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    first = True
    for item in items:
        level = 0
        text = item
        if isinstance(item, tuple):
            level, text = item
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        paragraph.level = level
        run = paragraph.add_run()
        run.text = ("• " if level == 0 else "– ") + text
        run.font.name = FONT
        run.font.size = Pt(size if level == 0 else size - 2)
        run.font.color.rgb = DARK if level == 0 else GRAY
        paragraph.space_after = Pt(9)


def add_picture_slide(slide, image_name: str, caption: str, left=Inches(0.7), top=Inches(1.3),
                      width=Inches(7.5)) -> None:
    path = SHOTS / image_name
    if path.exists():
        slide.shapes.add_picture(str(path), left, top, width=width)
    box = slide.shapes.add_textbox(left, top + Inches(4.35), width, Inches(0.5))
    box.text_frame.text = caption
    style_text(box.text_frame, 12, GRAY, align=PP_ALIGN.CENTER)


def add_table(slide, data, left=Inches(0.7), top=Inches(1.35), width=Inches(11.9),
              height=Inches(4.6), font_size=13, header_color=NAVY) -> None:
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = shape.table
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            cell.margin_left = Inches(0.08)
            cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04)
            cell.margin_bottom = Inches(0.04)
            frame = cell.text_frame
            frame.word_wrap = True
            for paragraph in frame.paragraphs:
                for run in paragraph.runs:
                    run.font.name = FONT
                    run.font.size = Pt(font_size)
                    run.font.color.rgb = WHITE if r == 0 else DARK
                    run.font.bold = r == 0
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_color if r == 0 else (
                RGBColor(0xF7, 0xFA, 0xFD) if r % 2 else WHITE)


prs = Presentation()
prs_width = prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ---------------------------------------------------------------- 封面
slide = blank_slide(prs)
background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs_width, prs.slide_height)
background.fill.solid()
background.fill.fore_color.rgb = NAVY
background.line.fill.background()

tag = slide.shapes.add_textbox(Inches(0.9), Inches(1.4), Inches(6), Inches(0.5))
tag.text_frame.text = "《企业级软件实践与工程能力提升训练营》课程设计"
style_text(tag.text_frame, 15, RGBColor(0xC5, 0xD6, 0xE6))

title = slide.shapes.add_textbox(Inches(0.9), Inches(2.0), Inches(11.5), Inches(1.6))
frame = title.text_frame
frame.word_wrap = True
frame.text = "LabCare 实验室设备预约与智能报修平台"
style_text(frame, 40, WHITE, bold=True)

subtitle = slide.shapes.add_textbox(Inches(0.9), Inches(3.7), Inches(11), Inches(0.8))
subtitle.text_frame.text = "全栈业务闭环  ·  RAG 知识问答  ·  Agent 确认后建单"
style_text(subtitle.text_frame, 20, RGBColor(0x9F, 0xC2, 0xE3))

meta = slide.shapes.add_textbox(Inches(0.9), Inches(5.5), Inches(11), Inches(1.2))
frame = meta.text_frame
team = load_team()
frame.text = (f"{team.get('group', '第 11 组')}　｜　{team.get('className', '【班级】')}　｜　"
              f"组长：{team.get('leader', '【组长姓名】')}　｜　成员：{member_names(team)}")
paragraph = frame.add_paragraph()
paragraph.text = "技术栈：Vue3 + Spring Boot 3.5 + MySQL 8 + LangChain + Chroma　｜　2026 年 11 月"
style_text(frame, 14, RGBColor(0xC5, 0xD6, 0xE6))

# ---------------------------------------------------------------- 背景与目标
slide = blank_slide(prs)
add_title_bar(slide, "项目背景与目标", "为什么做这个系统")
add_bullets(slide, [
    "现状问题：设备信息查不到、预约状态不透明、故障处理进度不可追踪、说明书与规范查找耗时",
    "业务痛点：纸质登记与即时通讯沟通导致重复预约、责任不清、历史记录难以追溯",
    "项目目标：把设备台账、预约审核、报修处理、知识问答放进同一个 Web 平台",
    "AI 定位：知识问答解决“资料找不到”，智能助手解决“报修填不对”，都限定在受控范围内",
    (1, "RAG：回答必须带来源，资料不足时明确说“无法确认”"),
    (1, "Agent：可以查设备、可以准备报修，但写入必须由用户确认后由后端执行"),
])

# ---------------------------------------------------------------- 范围
slide = blank_slide(prs)
add_title_bar(slide, "范围与取舍", "一周内可交付、可演示、可验收")
add_table(slide, [
    ["本期实现（P0）", "本期不实现", "取舍理由"],
    ["登录鉴权、设备台账、预约申请与审核", "统一身份认证、复杂排课调度", "课程原型聚焦单实验室业务闭环"],
    ["报修提交、受理、处理、完成/关闭", "物联网传感器、自动故障诊断", "无硬件条件，避免无法验证的功能"],
    ["知识库上传、索引、带引用问答", "扫描版 PDF OCR、图片识别", "保证链路可复现，多模态列为加分项"],
    ["Agent 查询设备、确认后建单", "多智能体协作、自动派单", "先保证单智能体工具调用真实可核验"],
], height=Inches(4.3))

# ---------------------------------------------------------------- 架构
slide = blank_slide(prs)
add_title_bar(slide, "总体架构", "四层结构，AI 能力可插拔")

layers = [
    ("表现层  Vue3 + Vite + Element Plus", "页面渲染 / 表单校验 / 会话交互", 1.35),
    ("业务层  Spring Boot 3.5 + JPA", "鉴权 · 权限 · 业务规则 · 事务 · 状态机 · AI 网关", 2.65),
    ("数据层  MySQL 8.0", "用户 · 设备 · 预约 · 工单 · 知识分片 · 会话与轨迹", 3.95),
    ("智能层  FastAPI + LangChain + Chroma", "解析切分 · 向量化 · 混合检索 · 工具调用", 5.25),
]
for index, (name, desc, top) in enumerate(layers):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.4), Inches(top),
                                 Inches(10.5), Inches(1.05))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT if index % 2 == 0 else RGBColor(0xE3, 0xED, 0xF7)
    box.line.color.rgb = BLUE
    frame = box.text_frame
    frame.margin_left = Inches(0.3)
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    paragraph = frame.paragraphs[0]
    run = paragraph.add_run()
    run.text = name
    run.font.name = FONT
    run.font.size = Pt(17)
    run.font.bold = True
    run.font.color.rgb = NAVY
    paragraph2 = frame.add_paragraph()
    run2 = paragraph2.add_run()
    run2.text = desc
    run2.font.name = FONT
    run2.font.size = Pt(12)
    run2.font.color.rgb = GRAY

note = slide.shapes.add_textbox(Inches(0.7), Inches(6.55), Inches(12), Inches(0.5))
note.text_frame.text = "边界约定：AI 服务不直接读写业务库；只通过内部令牌调用只读工具与建单前校验；写操作由后端在用户确认后执行"
style_text(note.text_frame, 12, GRAY)

# ---------------------------------------------------------------- 业务闭环
slide = blank_slide(prs)
add_title_bar(slide, "核心业务闭环", "预约与报修两条主链路")
left = slide.shapes.add_textbox(Inches(0.7), Inches(1.3), Inches(5.9), Inches(5.2))
frame = left.text_frame
frame.word_wrap = True
frame.text = "设备预约"
style_text(frame, 20, NAVY, bold=True)
for step in ["1  查询设备详情与可预约信息",
             "2  选择时段提交（30 分钟粒度 / 提前 30 分钟 / 最多 7 天）",
             "3  校验时间合法性与已批准预约冲突",
             "4  管理员审核，批准时在设备行锁内二次校验",
             "5  用户查看结果；结束后标记完成"]:
    paragraph = frame.add_paragraph()
    paragraph.text = step
    style_text(frame, 14, DARK)
    paragraph.space_before = Pt(8)

right = slide.shapes.add_textbox(Inches(6.9), Inches(1.3), Inches(5.9), Inches(5.2))
frame = right.text_frame
frame.word_wrap = True
frame.text = "故障报修"
style_text(frame, 20, NAVY, bold=True)
for step in ["1  选择设备，填写故障描述与联系方式",
             "2  生成唯一工单号，状态“待受理”",
             "3  管理员受理 → “处理中”，可填写处理记录",
             "4  填写处理结果 → “已完成”；无效工单“已关闭”",
             "5  用户查看状态与完整处理轨迹"]:
    paragraph = frame.add_paragraph()
    paragraph.text = step
    style_text(frame, 14, DARK)
    paragraph.space_before = Pt(8)

# ---------------------------------------------------------------- 技术选型
slide = blank_slide(prs)
add_title_bar(slide, "技术选型", "课程固定技术栈 + 可离线复现的 AI 方案")
add_table(slide, [
    ["层次", "选型", "关键理由"],
    ["前端", "Vue 3 + Vite + Element Plus + Pinia", "组合式 API 提效，组件覆盖管理端场景"],
    ["后端", "Spring Boot 3.5.16（Java 21）+ Spring Data JPA", "事务与分层清晰，便于演示业务规则下沉"],
    ["鉴权", "自实现 HS256 JWT + 拦截器", "仅用 JDK 加密库，避免引入完整安全框架的复杂度"],
    ["数据库", "MySQL 8.0（InnoDB / utf8mb4）", "支持事务与行锁，可演示并发冲突控制"],
    ["AI 服务", "FastAPI + LangChain 1.x + Chroma", "Prompt 与工具编排标准化，向量库可持久化"],
    ["检索", "字符 n-gram 哈希向量 + BM25 重排", "无需下载模型即可离线重建索引，答辩环境可复现"],
    ["大模型", "DeepSeek（OpenAI 兼容）", "中文效果好；未配置 Key 时自动降级为检索摘要"],
], height=Inches(4.9), font_size=12.5)

# ---------------------------------------------------------------- 数据库
slide = blank_slide(prs)
add_title_bar(slide, "数据库设计", "11 张表支撑业务与 AI 留痕")
add_table(slide, [
    ["表", "作用", "关键约束 / 索引"],
    ["app_user", "用户与角色（USER / ADMIN）", "username 唯一；BCrypt 密码摘要"],
    ["equipment", "设备台账", "code 业务唯一；(category, laboratory, status) 索引"],
    ["reservation", "预约申请与审核", "(equipment_id, start_time, end_time) 支撑冲突查询"],
    ["repair_ticket", "报修工单与处理结果", "code 唯一；source 区分手动 / 智能助手"],
    ["operation_log", "关键操作留痕", "按 target_type + target_id 查询轨迹"],
    ["knowledge_document / chunk", "知识文档与分片原文", "分片回存用于引用溯源与重建索引"],
    ["chat_session / message / agent_run", "AI 会话与工具轨迹", "支持会话回看与执行过程核验"],
    ["pending_action", "Agent 待确认动作", "token 唯一；10 分钟过期；一次性消费"],
], height=Inches(5.0), font_size=12)

# ---------------------------------------------------------------- 运行结果 1
slide = blank_slide(prs)
add_title_bar(slide, "运行结果：设备台账与预约", "真实前后端与数据库联动")
add_picture_slide(slide, "03-设备台账.png", "设备台账：关键词、类别、状态筛选与分页", width=Inches(6.6))
add_picture_slide(slide, "12-我的预约.png", "我的预约：状态、审核意见与时段信息",
                  left=Inches(7.5), width=Inches(5.2))

# ---------------------------------------------------------------- 运行结果 2
slide = blank_slide(prs)
add_title_bar(slide, "运行结果：管理端审核与工单", "权限隔离与状态机")
add_picture_slide(slide, "14-预约审核.png", "预约审核：通过/驳回，驳回必填意见", width=Inches(6.6))
add_picture_slide(slide, "15-工单处理.png", "工单处理：受理、处理记录、完成/关闭",
                  left=Inches(7.5), width=Inches(5.2))

# ---------------------------------------------------------------- RAG
slide = blank_slide(prs)
add_title_bar(slide, "AI 能力一：RAG 知识问答", "带来源、可溯源、敢于说“不知道”")
add_picture_slide(slide, "06-RAG问答与引用.png", "回答下方列出文档、片段序号、相关度与原文摘要", width=Inches(6.5))
add_bullets(slide, [
    "语料：设备手册、安全规范、故障指南（首次索引 16 个分片）",
    "切分：块 320 字 / 重叠 60 字，中文标点分隔",
    "检索：Chroma 向量召回 Top-10 → BM25 重排 → Top-4",
    "生成：Prompt 强制只依据资料作答，关键结论标注 [1][2]",
    "拒答：覆盖率不足或无词法命中时回答“现有资料无法确认”",
    "降级：无模型 Key 时返回原文摘要，界面明确标注",
], left=Inches(7.5), width=Inches(5.3), top=Inches(1.4), size=14)

# ---------------------------------------------------------------- Agent
slide = blank_slide(prs)
add_title_bar(slide, "AI 能力二：Agent 工具调用与确认建单", "可规划、可执行、写入受控")
add_picture_slide(slide, "08-Agent待确认.png", "展示待提交内容，此时数据库中还没有工单", width=Inches(6.5))
add_picture_slide(slide, "09-Agent工具调用轨迹.png", "每一步工具调用的入参、返回与成功状态可展开查看",
                  left=Inches(7.5), width=Inches(5.2), top=Inches(1.3))

# ---------------------------------------------------------------- 安全边界
slide = blank_slide(prs)
add_title_bar(slide, "安全边界与可靠性设计", "AI 不能越过的四条线")
add_bullets(slide, [
    "工具白名单：search_equipment / get_equipment / prepare_repair，无任何写接口",
    "写操作确认：prepare_repair 只生成预览，用户确认后由后端以当前登录身份建单",
    "令牌一次性：UUID + 10 分钟过期 + 归属校验 + 重复确认幂等",
    "服务间隔离：AI 调用 /internal/** 必须携带 X-Internal-Token",
    "降级可用：AI 服务停机时问答返回 503 明确提示，设备、预约、手动报修不受影响",
    "数据留痕：审核、状态流转、Agent 建单全部写入 operation_log / agent_run",
])

# ---------------------------------------------------------------- 测试
slide = blank_slide(prs)
add_title_bar(slide, "测试与验收", "自动化覆盖负向与异常场景")
add_table(slide, [
    ["测试集", "覆盖范围", "结果"],
    ["tests/api_smoke.py", "AT-01~AT-11：设备、预约冲突、报修流转、越权、RAG 引用、Agent 确认与幂等", "26 / 26 通过"],
    ["tests/ai_down_check.py", "AI 服务停机后：问答 503、基础业务仍可用", "4 / 4 通过"],
    ["src/frontend/scripts/ui_smoke.mjs", "浏览器端到端：登录、台账、RAG、Agent 取消与建单、管理端", "16 / 16 通过，控制台错误 0"],
    ["人工核对", "状态标签、空状态、错误提示、审计轨迹", "与预期一致"],
], height=Inches(3.2), font_size=13)

note = slide.shapes.add_textbox(Inches(0.7), Inches(5.0), Inches(11.9), Inches(1.6))
frame = note.text_frame
frame.word_wrap = True
frame.text = "证据位置：测试结果.xlsx ｜ evidence/测试与构建/（接口与 UI 报告）｜ evidence/运行截图或录屏/（18 张截图）｜ evidence/Agent执行轨迹/ ｜ evidence/RAG检索验证/"
style_text(frame, 12, GRAY)

# ---------------------------------------------------------------- 分工
slide = blank_slide(prs)
add_title_bar(slide, "分工与个人贡献", "详细成果位置见 成员任务表.xlsx")
team_rows = [["成员", "负责模块", "主要成果"]]
for member in team["members"]:
    label = member["name"] + ("（组长）" if member.get("role") == "组长" else "")
    team_rows.append([label, member.get("module", ""), member.get("pptBrief") or member.get("achievement", "")])
add_table(slide, team_rows, height=Inches(3.0), font_size=13)

# ---------------------------------------------------------------- 总结
slide = blank_slide(prs)
add_title_bar(slide, "总结与展望", "做得扎实的地方与下一步")
add_bullets(slide, [
    "业务规则下沉：预约冲突、状态机、权限校验都在后端，前端只负责展示与交互",
    "AI 可解释、可兜底：RAG 强制引用与拒答，Agent 只提案不写库，模型不可用不影响业务",
    "可验证性：把验收场景脚本化，配合截图与报告，功能是否可用可以当场复现",
    "不足：哈希向量的语义泛化弱于句向量模型；缺少站内通知；未做容器化",
    "下一步：接入本地 embedding 模型并保留混合检索；补充消息通知与统计数据看板",
    "扩展：故障照片识别作为加分项，不进入主演示链路",
])

prs.save(OUTPUT)
print(f"已生成 {OUTPUT}（{len(prs.slides.__iter__.__self__._sldIdLst)} 张幻灯片）")


