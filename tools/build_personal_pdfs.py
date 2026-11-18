"""Create print-ready personal report PDFs from the Markdown sources."""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "个人材料"
NAMES = ("郑颖浩", "常辰", "赵佳伟")
CLASS_PLACEHOLDER = "软件班级"
pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))

body = ParagraphStyle("body", fontName="SimHei", fontSize=9.4, leading=15.8, spaceAfter=5)
title = ParagraphStyle("title", parent=body, fontSize=18, leading=25, spaceAfter=12)
heading = ParagraphStyle("heading", parent=body, fontSize=12, leading=18, spaceBefore=10, spaceAfter=6, keepWithNext=True)
cell_style = ParagraphStyle("cell", parent=body, fontSize=8.3, leading=12.8, spaceAfter=0, splitLongWords=True)


def inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font color='#34495e'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def make_table(lines):
    rows = [[x.strip() for x in line.strip().strip("|").split("|")] for line in lines]
    rows = [r for r in rows if not all(re.fullmatch(r"[- :]+", c or "") for c in r)]
    ncols = max(len(r) for r in rows)
    widths = {2: [42 * mm, 128 * mm], 3: [44 * mm, 65 * mm, 61 * mm]}.get(ncols)
    if widths is None:
        widths = [170 * mm / ncols] * ncols
    data = [[Paragraph(inline(row[i] if i < len(row) else ""), cell_style) for i in range(ncols)] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EEF3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4CC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def footer(canvas, doc):
    canvas.setFont("SimHei", 8)
    canvas.setFillColor(colors.HexColor("#66727D"))
    canvas.drawRightString(A4[0] - 22 * mm, 13 * mm, f"第 {doc.page} 页")


def build(name):
    source = MATERIALS / f"{CLASS_PLACEHOLDER}-{name}-个人报告.md"
    output = MATERIALS / f"{CLASS_PLACEHOLDER}-{name}-个人报告.pdf"
    lines = source.read_text(encoding="utf-8").splitlines()
    story = []
    current_section = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), title))
        elif line.startswith("## "):
            current_section = line[3:]
            story.append(Paragraph(inline(current_section), heading))
        elif line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            story.append(make_table(block))
            story.append(Spacer(1, 5))
            if current_section.startswith("四、"):
                story.append(PageBreak())
            continue
        elif line.startswith("- "):
            story.append(Paragraph("• " + inline(line[2:]), body))
        else:
            story.append(Paragraph(inline(line), body))
        i += 1
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm,
                            title=f"{name}个人报告", author=name)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(output)


if __name__ == "__main__":
    for person in NAMES:
        build(person)
