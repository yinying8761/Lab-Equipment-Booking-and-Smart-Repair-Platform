"""把设计阶段的确认结论回写到需求文档（版本 V1.1），保持需求、文档、源码一致。

用法：python tools/update_requirements_doc.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "第11组-实验室设备预约与智能报修平台-需求文档.docx"

DECISIONS = [
    ("技术栈", "前端 Vue 3 + Vite + Element Plus；后端 Spring Boot 3.5（Java 21）+ MySQL 8；"
               "AI 服务 Python FastAPI + LangChain + Chroma，作为独立服务交付"),
    ("模型服务", "DeepSeek（OpenAI 兼容接口），密钥仅通过本地配置或环境变量注入；"
                 "未配置 Key 时自动降级为检索原文摘要，界面明确标注"),
    ("向量存储", "本地持久化 Chroma + 字符 n-gram 哈希向量，检索时结合 BM25 词法重排；"
                 "无需下载模型即可离线重建索引"),
    ("预约规则", "时间粒度 30 分钟；至少提前 30 分钟、最多提前 7 天；单次 0.5~4 小时；"
                 "待审核申请不占用时段，批准时在设备行锁内二次校验冲突"),
    ("知识文档", "支持 txt / md / pdf / docx，单文件不超过 10MB；暂不支持扫描版 PDF（无 OCR）"),
    ("角色合并", "课程原型将实验室管理员与维修人员合并为单一管理员角色，仅保留普通用户与管理员两种角色"),
    ("多模态", "本期不纳入主链路；如后续时间允许，仅作为可选加分项（故障照片生成描述草稿，不自动诊断）"),
]


def main() -> None:
    document = Document(str(DOC))

    # 版本号
    for table in document.tables:
        for row in table.rows:
            cells = row.cells
            if cells and cells[0].text.strip() == "文档版本":
                cell = cells[1]
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if "V1.0" in run.text:
                            run.text = run.text.replace("V1.0", "V1.1")

    # 追加确认结论
    heading = document.add_paragraph()
    heading.style = document.styles["Heading 2"]
    run = heading.add_run("9.3 设计阶段确认结论（V1.1）")
    run.font.name = "黑体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    run.font.size = Pt(12.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(46, 116, 181)

    intro = document.add_paragraph()
    intro_run = intro.add_run("以下各项为 9.2 待确认问题在概要设计阶段的最终结论，后续实现、测试与演示材料均以此为准。")
    intro_run.font.name = "宋体"
    intro_run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    intro_run.font.size = Pt(10.5)

    for name, text in DECISIONS:
        paragraph = document.add_paragraph(style="List Bullet")
        bold = paragraph.add_run(name + "：")
        bold.font.name = "宋体"
        bold._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        bold.font.size = Pt(10.5)
        bold.font.bold = True
        body = paragraph.add_run(text)
        body.font.name = "宋体"
        body._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        body.font.size = Pt(10.5)

    document.save(str(DOC))
    print(f"已更新 {DOC}")


if __name__ == "__main__":
    main()
