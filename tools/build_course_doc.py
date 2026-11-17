"""把 docs/课设文档.md 渲染为符合课程模板风格的 DOCX。

用法：python tools/build_course_doc.py
输出：课设文档-实验室设备预约与智能报修平台.docx（项目根目录）
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from team_loader import load_team, member_names

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "课设文档.md"
OUTPUT = ROOT / "课设文档-实验室设备预约与智能报修平台.docx"

PRIMARY = (31, 78, 121)
SECONDARY = (46, 116, 181)


def set_run_font(run, name: str = "宋体", size: float = 10.5, bold: bool = False,
                 color: tuple[int, int, int] | None = None) -> None:
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_page_number_footer(section) -> None:
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("第 ")
    set_run_font(run, size=9, color=(120, 120, 120))
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    paragraph._p.append(fld)
    run2 = paragraph.add_run(" 页")
    set_run_font(run2, size=9, color=(120, 120, 120))


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def add_cover(doc: Document) -> None:
    for _ in range(3):
        doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("课程设计文档")
    set_run_font(run, "黑体", 26, True, PRIMARY)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("实验室设备预约与智能报修平台")
    set_run_font(run, "黑体", 22, True, SECONDARY)

    doc.add_paragraph()
    team = load_team()
    info = doc.add_table(rows=6, cols=2)
    info.style = "Table Grid"
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows = [
        ("项目组别", team.get("group", "第 11 组")),
        ("课题名称", team.get("systemName", "实验室设备预约与智能报修平台")),
        ("技术方向", "AI + 全栈 + 智能体 + RAG"),
        ("组长班级 / 姓名", f"{team.get('className', '【班级】')} / {team.get('leader', '【组长姓名】')}"),
        ("小组成员", member_names(team)),
        ("文档版本 / 日期", "V1.0 / 2026 年 11 月"),
    ]
    for index, (key, value) in enumerate(rows):
        left, right = info.rows[index].cells
        left.text = ""
        right.text = ""
        set_run_font(left.paragraphs[0].add_run(key), "黑体", 11, True, PRIMARY)
        set_run_font(right.paragraphs[0].add_run(value), "宋体", 11)
        shade_cell(left, "EEF3F9")
        left.width = Inches(1.7)
        right.width = Inches(3.6)

    for _ in range(4):
        doc.add_paragraph()
    note = doc.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(note.add_run("配套材料：需求规格说明书、源码工程、答辩 PPT"), "宋体", 9, color=(120, 120, 120))

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


INLINE_BOLD = re.compile(r"\*\*(.+?)\*\*")
INLINE_CODE = re.compile(r"`(.+?)`")


def add_inline(paragraph, text: str, size: float = 10.5) -> None:
    """支持 **加粗** 与 `行内代码` 的简单行内解析。"""
    tokens = re.split(r"(\*\*.+?\*\*|`.+?`)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            set_run_font(paragraph.add_run(token[2:-2]), size=size, bold=True)
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            set_run_font(run, "Consolas", size - 1)
            run.font.color.rgb = RGBColor(180, 60, 40)
        else:
            set_run_font(paragraph.add_run(token), size=size)


def add_table(doc: Document, rows: list[list[str]]) -> None:
    header, body = rows[0], rows[1:]
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for index, text in enumerate(header):
        cell = table.rows[0].cells[index]
        cell.text = ""
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(paragraph.add_run(text), "黑体", 9, True, (255, 255, 255))
        shade_cell(cell, "1F4E79")
    for row in body:
        cells = table.add_row().cells
        for index, text in enumerate(row[: len(header)]):
            cell = cells[index]
            cell.text = ""
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(1)
            add_inline(paragraph, text, size=9)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_image(doc: Document, path: Path, caption: str) -> None:
    if not path.exists():
        paragraph = doc.add_paragraph()
        set_run_font(paragraph.add_run(f"（缺少图片：{path.name}）"), size=9, color=(200, 60, 60))
        return
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(path), width=Inches(6.0))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(cap.add_run(caption), size=9, color=(110, 110, 110))


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    add_page_number_footer(section)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(6)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(header.add_run("实验室设备预约与智能报修平台｜课程设计文档"), size=8, color=(120, 120, 120))

    add_cover(doc)

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        # 代码块
        if stripped.startswith("```"):
            index += 1
            block = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            index += 1
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.2)
            paragraph.paragraph_format.line_spacing = 1.15
            for position, code_line in enumerate(block):
                run = paragraph.add_run(code_line)
                set_run_font(run, "Consolas", 9)
                if position < len(block) - 1:
                    run.add_break()
            continue

        # 表格
        if stripped.startswith("|"):
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index].strip())
                index += 1
            rows = []
            for raw in block:
                if re.fullmatch(r"\|[\s:\-|]+\|", raw):
                    continue
                cells = [cell.strip() for cell in raw.strip("|").split("|")]
                rows.append(cells)
            if rows:
                add_table(doc, rows)
            continue

        # 图片
        image_match = re.match(r"!\[(.*?)\]\((.+?)\)", stripped)
        if image_match:
            caption, relative = image_match.groups()
            add_image(doc, (SOURCE.parent / relative).resolve(), caption)
            index += 1
            continue

        # 标题
        heading_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            if level == 1:
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.space_before = Pt(14)
                paragraph.paragraph_format.space_after = Pt(8)
                set_run_font(paragraph.add_run(text), "黑体", 18, True, PRIMARY)
            elif level == 2:
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.space_before = Pt(12)
                paragraph.paragraph_format.space_after = Pt(6)
                set_run_font(paragraph.add_run(text), "黑体", 14, True, PRIMARY)
            elif level == 3:
                paragraph = doc.add_paragraph()
                paragraph.paragraph_format.space_before = Pt(8)
                set_run_font(paragraph.add_run(text), "黑体", 12, True, SECONDARY)
            else:
                paragraph = doc.add_paragraph()
                set_run_font(paragraph.add_run(text), "黑体", 11, True, (70, 70, 70))
            index += 1
            continue

        # 引用
        if stripped.startswith(">"):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.25)
            add_inline(paragraph, stripped.lstrip("> ").strip(), size=9.5)
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor(110, 110, 110)
            index += 1
            continue

        # 有序列表
        ordered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if ordered:
            paragraph = doc.add_paragraph(style="List Number")
            add_inline(paragraph, ordered.group(2))
            index += 1
            continue

        # 无序列表
        if stripped.startswith("- "):
            paragraph = doc.add_paragraph(style="List Bullet")
            add_inline(paragraph, stripped[2:])
            index += 1
            continue

        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Inches(0.28)
        add_inline(paragraph, stripped)
        index += 1

    doc.save(OUTPUT)
    print(f"已生成 {OUTPUT}")


if __name__ == "__main__":
    build()
