"""一键替换班级与三人学号，并重新生成三件套。

用法：
    python tools/apply_member_info.py --class 软件2201班 \
        --ids "郑颖浩=20220101,常辰=20220102,赵佳伟=20220103"

说明：只修改 docs/team.json 并重建 课设文档.docx / 成员任务表.xlsx / 答辩PPT.pptx，
业务代码与测试证据不受影响。不传 --ids 时仅更新班级。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_FILE = ROOT / "docs" / "team.json"
PYTHON = sys.executable


def parse_ids(raw: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise SystemExit(f"学号格式应为 姓名=学号，收到：{chunk}")
        name, value = chunk.split("=", 1)
        mapping[name.strip()] = value.strip()
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="class_name", help="组长班级，例如 软件2201班")
    parser.add_argument("--ids", help='学号映射，例如 "郑颖浩=20220101,常辰=20220102,赵佳伟=20220103"')
    parser.add_argument("--skip-build", action="store_true", help="只更新 team.json，不重建文档")
    args = parser.parse_args()

    if not TEAM_FILE.exists():
        raise SystemExit(f"未找到 {TEAM_FILE}")

    team = json.loads(TEAM_FILE.read_text(encoding="utf-8"))
    changed = []

    if args.class_name:
        team["className"] = args.class_name.strip()
        changed.append(f"班级 -> {team['className']}")

    if args.ids:
        mapping = parse_ids(args.ids)
        known = {member["name"] for member in team["members"]}
        unknown = set(mapping) - known
        if unknown:
            raise SystemExit(f"team.json 中没有这些成员：{'、'.join(sorted(unknown))}")
        for member in team["members"]:
            if member["name"] in mapping:
                member["studentId"] = mapping[member["name"]]
                changed.append(f"{member['name']} 学号 -> {mapping[member['name']]}")

    TEAM_FILE.write_text(json.dumps(team, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已更新 docs/team.json：")
    for item in changed or ["（无变化）"]:
        print("  -", item)

    if args.skip_build:
        print("按参数跳过重建。")
        return 0

    for script in ("build_course_doc.py", "build_deliverables.py", "build_ppt.py"):
        print(f"运行 {script} ...")
        result = subprocess.run([PYTHON, str(ROOT / "tools" / script)], cwd=ROOT)
        if result.returncode != 0:
            print(f"{script} 失败，退出码 {result.returncode}")
            return result.returncode

    print("\n完成。剩余手工步骤：把个人报告导出 PDF 放入 个人材料/，再运行 scripts/pack.ps1 打包。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
