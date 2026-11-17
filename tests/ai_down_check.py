"""AT-11 验证脚本：AI 服务不可用时的降级行为。

用法（先停掉 8100 端口的 AI 服务）：
    python tests/ai_down_check.py
预期：
    1. /ai/chat 返回 503，提示 AI 服务不可用，且不伪造答案；
    2. 设备查询、预约、手动报修等基础业务仍然正常；
    3. 结果写入 evidence/测试与构建/ai_degradation_report.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evidence" / "测试与构建" / "ai_degradation_report.json"
BASE = "http://127.0.0.1:8080/api"

results = []


def record(case: str, passed: bool, detail: str) -> None:
    results.append({"case": case, "passed": passed, "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {case} :: {detail}")


def main() -> int:
    session = requests.Session()

    def call(method, path, token=None, body=None):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = session.request(method, f"{BASE}{path}", headers=headers, json=body, timeout=30)
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, {"raw": response.text}

    status, body = call("POST", "/auth/login", body={"username": "student01", "password": "Student@123"})
    token = body["data"]["token"]

    status, body = call("POST", "/ai/chat", token, {"question": "离心机报 E07 怎么处理？"})
    record("AT-11a", status == 503 and not body.get("data"),
           f"HTTP {status}：{body.get('message')}")

    status, body = call("POST", "/ai/agent/chat", token, {"message": "EQ-002 帮我报修"})
    record("AT-11b", status == 503 and not body.get("data"),
           f"HTTP {status}：{body.get('message')}")

    status, body = call("GET", "/equipments?keyword=离心", token)
    record("AT-11c", status == 200 and body["data"]["total"] >= 1,
           f"设备查询仍可用，命中 {body.get('data', {}).get('total')} 台")

    status, body = call("POST", "/repairs", token,
                        {"equipmentId": 2, "description": "降级演练：AI 不可用时手动提交报修", "contact": "13800000001"})
    record("AT-11d", status == 200 and body.get("data", {}).get("code"),
           f"手动报修仍可用，工单号 {body.get('data', {}).get('code')}")

    passed = sum(1 for item in results if item["passed"])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scenario": "AI 服务停止后系统降级行为",
        "total": len(results),
        "passed": passed,
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n== {len(results)} 项，通过 {passed} 项；报告 {REPORT}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
