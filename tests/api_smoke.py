"""LabCare 接口冒烟测试 / 验收场景自动化。

用法：
    python tests/api_smoke.py            # 运行全部场景
    python tests/api_smoke.py --base http://127.0.0.1:8080/api

前置条件：MySQL 已执行 db/init.sql，后端与 AI 服务已启动。
结果同时写入 evidence/测试与构建/api_smoke_report.json。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evidence" / "测试与构建" / "api_smoke_report.json"

RESULTS: list[dict] = []


def record(case: str, title: str, passed: bool, detail: str) -> None:
    RESULTS.append({"case": case, "title": title, "passed": passed, "detail": detail})
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {case} {title} :: {detail}")


class Api:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.session = requests.Session()

    def call(self, method: str, path: str, token: str | None = None, body=None, files=None, timeout=120):
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"{self.base}{path}"
        if files is not None:
            response = self.session.request(method, url, headers=headers, data=body, files=files, timeout=timeout)
        else:
            response = self.session.request(method, url, headers=headers, json=body, timeout=timeout)
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        return response.status_code, payload

    def login(self, username: str, password: str) -> str:
        status, body = self.call("POST", "/auth/login", body={"username": username, "password": password})
        assert status == 200 and body["code"] == 0, f"登录失败 {username}: {status} {body}"
        return body["data"]["token"]


def next_slot(hours_from_now: int = 2) -> tuple[str, str]:
    """返回满足 30 分钟粒度、至少提前 30 分钟的起止时间。"""
    now = datetime.now()
    base = (now + timedelta(hours=hours_from_now)).replace(minute=0, second=0, microsecond=0)
    minute = 30 if base.minute < 30 else 0
    if minute == 0 and base.minute >= 30:
        base += timedelta(hours=1)
    base = base.replace(minute=minute)
    if base < now + timedelta(minutes=35):
        base += timedelta(minutes=30)
    end = base + timedelta(hours=1)
    fmt = "%Y-%m-%d %H:%M:%S"
    return base.strftime(fmt), end.strftime(fmt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8080/api")
    args = parser.parse_args()
    api = Api(args.base)

    print("== 登录三个演示账号 ==")
    student1 = api.login("student01", "Student@123")
    student2 = api.login("student02", "Student@123")
    admin = api.login("admin", "Admin@123")

    # ---------------- AT-01 设备查询 ----------------
    status, body = api.call("GET", "/equipments?keyword=离心&page=1&size=5", student1)
    items = body.get("data", {}).get("list", [])
    ok = status == 200 and body["code"] == 0 and len(items) >= 1
    record("AT-01", "设备列表与详情", ok, f"关键词=离心 命中 {len(items)} 台")
    if items:
        eq = items[0]
        status, body = api.call("GET", f"/equipments/{eq['id']}", student1)
        detail = body.get("data", {})
        ok = status == 200 and detail.get("code") == eq["code"] and detail.get("usageNote")
        record("AT-01b", "设备详情字段完整", ok, f"{detail.get('code')} {detail.get('name')} 状态={detail.get('statusLabel')}")

    # 空结果
    status, body = api.call("GET", "/equipments?keyword=不存在的设备XYZ", student1)
    ok = status == 200 and body["data"]["total"] == 0
    record("AT-01c", "无匹配显示空状态", ok, f"total={body.get('data', {}).get('total')}")

    # ---------------- AT-02 预约全流程 ----------------
    # 依次尝试多个未来时段，避免上一次运行留下的预约造成冲突
    reservation = None
    start = end = None
    equipment_id = 3
    for attempt in range(8):
        candidate_start, candidate_end = next_slot(2 + attempt * 3)
        status, body = api.call("POST", "/reservations", student1,
                                {"equipmentId": equipment_id, "startTime": candidate_start,
                                 "endTime": candidate_end, "purpose": "自动化测试预约"})
        if status == 200 and body.get("code") == 0:
            reservation = body["data"]
            start, end = candidate_start, candidate_end
            break
        if status != 409:
            break
    ok = reservation is not None
    record("AT-02", "提交预约", ok,
           f"{reservation.get('code') if reservation else '-'} {start}~{end} "
           f"状态={reservation.get('statusLabel') if reservation else '-'}")

    if ok:
        status, body = api.call("POST", f"/admin/reservations/{reservation['id']}/review", admin,
                                {"approve": True, "comment": "自动化测试：同意"})
        ok2 = status == 200 and body["data"]["status"] == "APPROVED"
        record("AT-02b", "管理员审核通过", ok2, body.get("data", {}).get("statusLabel", body.get("message")))
        status, body = api.call("GET", f"/reservations/{reservation['id']}", student1)
        ok3 = body["data"]["status"] == "APPROVED" and body["data"]["reviewComment"]
        record("AT-02c", "用户查看审核结果", ok3,
               f"状态={body['data']['statusLabel']} 意见={body['data']['reviewComment']}")

    # ---------------- AT-03 非法时间与冲突 ----------------
    status, body = api.call("POST", "/reservations", student1,
                            {"equipmentId": 3, "startTime": end, "endTime": start, "purpose": "时间倒置"})
    ok = status == 400 and body["code"] == 400
    record("AT-03", "非法时间范围被拒绝", ok, body.get("message", ""))

    status, body = api.call("POST", "/reservations", student2,
                            {"equipmentId": 3, "startTime": start, "endTime": end, "purpose": "冲突预约"})
    ok = status == 409
    record("AT-03b", "与已批准预约冲突被拒绝", ok, body.get("message", ""))

    # 待审核不占用时段：先提交 PENDING，再让另一个用户在重叠时段提交（应允许）
    s2, e2 = next_slot(6)
    status, body = api.call("POST", "/reservations", student2,
                            {"equipmentId": 4, "startTime": s2, "endTime": e2, "purpose": "待审核不占用"})
    ok1 = status == 200
    pending_id = body.get("data", {}).get("id")
    status, body = api.call("POST", "/reservations", student1,
                            {"equipmentId": 4, "startTime": s2, "endTime": e2, "purpose": "重叠但均未批准"})
    ok2 = status == 200
    record("AT-03c", "待审核申请互不占用时段", ok1 and ok2, f"两条重叠申请均可提交：{ok1 and ok2}")
    # 撤回这条待审核预约，避免影响后续
    if pending_id:
        api.call("POST", f"/reservations/{pending_id}/cancel", student2)
    if ok2:
        api.call("POST", f"/reservations/{body['data']['id']}/cancel", student1)

    # ---------------- AT-04 报修全流程 ----------------
    status, body = api.call("POST", "/repairs", student1,
                            {"equipmentId": 2, "description": "自动化测试：电镜真空度达不到设定值，提示 VACUUM TIMEOUT",
                             "contact": "13800000001"})
    ok = status == 200 and body["code"] == 0
    repair = body.get("data", {})
    record("AT-04", "提交报修生成工单", ok, f"{repair.get('code')} 状态={repair.get('statusLabel')}")

    if ok:
        status, body = api.call("POST", f"/admin/repairs/{repair['id']}/accept", admin)
        ok1 = status == 200 and body["data"]["status"] == "PROCESSING"
        status, body = api.call("POST", f"/admin/repairs/{repair['id']}/complete", admin,
                                {"resolution": "自动化测试：已清洗真空腔并更换密封圈，抽真空正常"})
        ok2 = status == 200 and body["data"]["status"] == "COMPLETED"
        status, body = api.call("GET", f"/repairs/{repair['id']}", student1)
        ok3 = body["data"]["status"] == "COMPLETED" and len(body["data"]["logs"]) >= 3
        record("AT-04b", "受理-处理-完成状态流转", ok1 and ok2 and ok3,
               f"轨迹条数={len(body['data']['logs'])} 状态={body['data']['statusLabel']}")

        # 非法状态跳转：已完成再受理
        status, body = api.call("POST", f"/admin/repairs/{repair['id']}/accept", admin)
        ok = status == 409
        record("AT-04c", "非法状态跳转被拒绝", ok, body.get("message", ""))

    # ---------------- AT-05 越权访问 ----------------
    status, body = api.call("GET", "/admin/repairs", student1)
    ok1 = status == 403
    status, body = api.call("GET", f"/repairs/{repair['id']}", student2)
    ok2 = status == 403
    status, body = api.call("GET", "/reservations/1", student2)
    ok3 = status == 403
    record("AT-05", "越权访问被后端拒绝", ok1 and ok2 and ok3, f"管理接口={ok1} 他人工单={ok2} 他人预约={ok3}")

    status, body = api.call("GET", "/equipments")
    record("AT-05b", "未登录访问被拒绝", status == 401, f"HTTP {status}")

    # ---------------- AT-06 / AT-07 RAG ----------------
    status, body = api.call("POST", "/ai/chat", student1, {"question": "离心机报 E07 怎么处理？"})
    data = body.get("data", {})
    ok = status == 200 and data.get("citations")
    record("AT-06", "RAG 命中并展示来源", bool(ok),
           f"引用 {len(data.get('citations', []))} 条；首要来源={data.get('citations', [{}])[0].get('title') if data.get('citations') else '-'}")
    rag_session = data.get("sessionId")

    status, body = api.call("POST", "/ai/chat", student1,
                            {"question": "今天中午食堂有什么菜？", "sessionId": rag_session})
    data = body.get("data", {})
    ok = status == 200 and not data.get("citations") and ("无法确认" in data.get("answer", ""))
    record("AT-07", "语料外问题明确说明证据不足", ok, data.get("answer", "")[:60])

    # ---------------- AT-08 新增文档后可检索 ----------------
    sample = ROOT / "data" / "测试数据" / "设备验收补充说明.md"
    with open(sample, "rb") as handle:
        status, body = api.call("POST", "/admin/knowledge/upload", admin,
                                body={"title": "设备验收补充说明（新增测试）"},
                                files={"file": (sample.name, handle, "text/markdown")})
    uploaded = body.get("data") or {}
    ok = status == 200 and uploaded.get("chunkCount", 0) > 0
    new_doc_id = uploaded.get("id")
    record("AT-08", "上传新文档并建立索引", ok,
           f"文档id={new_doc_id} 分片={uploaded.get('chunkCount')} 状态={uploaded.get('statusLabel')}")

    if new_doc_id:
        status, body = api.call("POST", "/ai/chat", student1,
                                {"question": "冷冻干燥机首次使用要预冷多久？"})
        data = body.get("data", {})
        hits = data.get("citations", [])
        matched = any(item.get("documentId") == new_doc_id for item in hits)
        ok = status == 200 and matched and "30" in data.get("answer", "")
        record("AT-08b", "新文档内容可被检索并引用", ok,
               f"引用命中新文档={matched}；答案含'30 分钟'={'30' in data.get('answer', '')}")

    # ---------------- AT-09 / AT-10 Agent ----------------
    status, body = api.call("POST", "/ai/agent/chat", student1,
                            {"message": "EQ-002 电镜真空度上不去，帮我报修"})
    data = body.get("data", {})
    confirm = data.get("confirm")
    ok = status == 200 and confirm is not None
    record("AT-09", "Agent 生成待确认报修预览", ok,
           f"工具步骤={len(data.get('trace', []))} 预览={(confirm or {}).get('preview', '')[:40]}")

    if confirm:
        before_status, before = api.call("GET", "/repairs/mine?page=1&size=50", student1)
        before_count = before["data"]["total"]
        status, body = api.call("POST", "/ai/agent/confirm", student1,
                                {"token": confirm["token"], "approved": False})
        after_status, after = api.call("GET", "/repairs/mine?page=1&size=50", student1)
        ok = status == 200 and after["data"]["total"] == before_count
        record("AT-09b", "取消确认不产生工单", ok,
               f"{before_count} -> {after['data']['total']} 条")

    status, body = api.call("POST", "/ai/agent/chat", student1,
                            {"message": "我要报修 EQ-003 紫外分光光度计，读数一直漂移，帮我准备报修单"})
    data = body.get("data", {})
    confirm = data.get("confirm")
    ok = status == 200 and confirm is not None
    record("AT-10", "Agent 再次生成待确认预览", ok, (confirm or {}).get("preview", "")[:50])

    if confirm:
        status, body = api.call("POST", "/ai/agent/confirm", student1,
                                {"token": confirm["token"], "approved": True})
        result = body.get("data", {})
        ok = status == 200 and result.get("repairCode")
        record("AT-10b", "确认后真实创建工单", ok,
               f"工单号={result.get('repairCode')} 返回={result.get('message')}")
        if ok:
            status, body = api.call("GET", "/repairs/mine?page=1&size=50", student1)
            codes = [item["code"] for item in body["data"]["list"]]
            record("AT-10c", "工单在列表中可查", result["repairCode"] in codes,
                   f"列表含 {result['repairCode']}")
            # 幂等：重复确认
            status, body = api.call("POST", "/ai/agent/confirm", student1,
                                    {"token": confirm["token"], "approved": True})
            ok = status == 200 and body["data"]["repairCode"] == result["repairCode"]
            record("AT-10d", "重复确认不重复建单", ok, body.get("data", {}).get("message", ""))

        # 管理员处理 Agent 创建的工单
        status, body = api.call("GET", "/admin/repairs?page=1&size=50", admin)
        target = next((x for x in body["data"]["list"] if x.get("source") == "AGENT"), None)
        record("AT-10e", "Agent 建单来源可追溯", target is not None,
               f"source={target.get('source') if target else '-'}")

    # ---------------- AT-11 异常不伪造成功 ----------------
    # AI 服务不可用时由人工/脚本停止服务后验证，这里检查接口错误码语义
    status, body = api.call("POST", "/ai/agent/confirm", student1, {"token": "not-a-real-token", "approved": True})
    ok = status == 404 and body["code"] == 404
    record("AT-11", "无效确认令牌被拒绝", ok, body.get("message", ""))

    # ---------------- 汇总 ----------------
    passed = sum(1 for item in RESULTS if item["passed"])
    total = len(RESULTS)
    print(f"\n== 共 {total} 项，通过 {passed} 项，失败 {total - passed} 项 ==")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base": args.base,
        "total": total,
        "passed": passed,
        "results": RESULTS,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"报告已写入 {REPORT}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
