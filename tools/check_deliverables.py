"""交付物完整性检查：打开 docx / pptx / xlsx，统计结构并确认关键章节存在。"""
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

ROOT = Path(r"F:\2026.11.2Project")

course = ROOT / "课设文档-实验室设备预约与智能报修平台.docx"
doc = Document(str(course))
headings = [p.text.strip() for p in doc.paragraphs if p.style.name.startswith("Heading") or p.text.strip()[:2] in
            ("1 ", "2 ", "3 ", "4 ", "5 ", "6 ", "7 ", "8 ", "9 ", "10")]
print(f"[docx] 段落 {len(doc.paragraphs)}，表格 {len(doc.tables)}，图片 {len(doc.inline_shapes)}")
text = "\n".join(p.text for p in doc.paragraphs)
for key in ["项目概述", "需求分析", "概要设计", "开发工具", "详细设计", "运行结果", "调试分析", "测试与验收结果", "总结与展望", "参考文献"]:
    print(f"  章节 {key}: {'有' if key in text else '缺失'}")

ppt = ROOT / "答辩PPT-实验室设备预约与智能报修平台.pptx"
prs = Presentation(str(ppt))
print(f"[pptx] 幻灯片 {len(prs.slides)} 页，尺寸 {prs.slide_width.inches:.2f}x{prs.slide_height.inches:.2f} 英寸")
picture_count = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
print(f"  图片 {picture_count} 张")

xlsx = ROOT / "测试结果.xlsx"
wb = load_workbook(xlsx)
for ws in wb.worksheets:
    print(f"[xlsx] {ws.title}: {ws.max_row} 行 x {ws.max_column} 列")
rows = list(wb["测试用例与结果"].iter_rows(min_row=2, values_only=True))
passed = sum(1 for r in rows if r[6] == "通过")
print(f"  用例 {len(rows)} 条，通过 {passed} 条")

member = load_workbook(ROOT / "成员任务表.xlsx")
print(f"[xlsx] 成员任务表: {member.active.max_row} 行")
