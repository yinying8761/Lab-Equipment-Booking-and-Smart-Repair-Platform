# 接口说明（后端 `/api`）

统一响应结构：

```json
{ "code": 0, "message": "success", "data": {}, "timestamp": "2026-11-09 11:00:00" }
```

- `code=0` 成功；`400` 参数或业务规则不满足；`401` 未登录；`403` 越权；`404` 不存在；`409` 状态冲突；`503` AI 服务不可用。
- 除登录与健康检查外，所有请求需携带 `Authorization: Bearer <token>`。
- 时间格式统一为 `yyyy-MM-dd HH:mm:ss`。

## 一、认证

| 方法 | 路径 | 请求体 | 响应 data |
| --- | --- | --- | --- |
| POST | `/auth/login` | `{username, password}` | `{token, user:{id, username, displayName, role, roleLabel}}` |
| GET | `/auth/me` | — | `user` |
| POST | `/auth/logout` | — | `{loggedOut:true}`（前端丢弃令牌即可） |

```bash
curl -X POST http://127.0.0.1:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"student01","password":"Student@123"}'
```

## 二、设备

| 方法 | 路径 | 参数 | 说明 |
| --- | --- | --- | --- |
| GET | `/equipments` | keyword, category, laboratory, status, page, size | 分页查询，status 取 AVAILABLE/MAINTENANCE/DISABLED |
| GET | `/equipments/{id}` | — | 详情 |
| GET | `/equipments/options` | keyword | 下拉选项与 Agent 工具使用 |
| POST | `/admin/equipments` | `{code,name,category,laboratory,location,status,description,usageNote}` | 新增（管理员） |
| PUT | `/admin/equipments/{id}` | 同上 | 编辑（管理员） |
| PATCH | `/admin/equipments/{id}/status` | `{status}` | 状态切换（管理员） |

## 三、预约

| 方法 | 路径 | 请求体 / 参数 | 说明 |
| --- | --- | --- | --- |
| POST | `/reservations` | `{equipmentId, startTime, endTime, purpose}` | 提交预约，返回 `code`、`status` |
| GET | `/reservations/equipment/{equipmentId}/reserved-time` | start, end（`yyyy-MM-dd HH:mm:ss`，范围 ≤ 31 天） | 该设备在区间内已占用（仅 APPROVED）的时段，升序 |
| GET | `/reservations/mine` | status, page, size | 本人预约 |
| GET | `/reservations/{id}` | — | 详情（本人或管理员） |
| POST | `/reservations/{id}/cancel` | — | 取消本人待审核预约 |
| GET | `/admin/reservations` | status, keyword, page, size | 管理员列表 |
| POST | `/admin/reservations/{id}/review` | `{approve:true/false, comment}` | 审核；驳回必填意见 |
| POST | `/admin/reservations/{id}/complete` | — | 结束后标记完成 |

错误示例：`409 所选时段与已有预约冲突（RS202611090001），请调整时间`。

## 四、报修

| 方法 | 路径 | 请求体 / 参数 | 说明 |
| --- | --- | --- | --- |
| POST | `/repairs` | `{equipmentId, description, contact}` | 提交报修 |
| GET | `/repairs/mine` | status, page, size | 本人工单 |
| GET | `/repairs/{id}` | — | 详情，含 `logs` 处理轨迹 |
| GET | `/admin/repairs` | status, keyword, page, size | 管理员列表 |
| POST | `/admin/repairs/{id}/accept` | — | 受理：PENDING → PROCESSING |
| POST | `/admin/repairs/{id}/progress` | `{resolution}` | 更新处理记录 |
| POST | `/admin/repairs/{id}/complete` | `{resolution}` | 完成，结果必填 |
| POST | `/admin/repairs/{id}/close` | `{reason}` | 关闭，原因必填 |

## 五、知识库（管理员）

| 方法 | 路径 | 请求 | 说明 |
| --- | --- | --- | --- |
| GET | `/admin/knowledge` | — | 文档列表（状态、分片数） |
| POST | `/admin/knowledge/upload` | multipart：`file`、可选 `title` | 支持 txt/md/pdf/docx，≤10MB |
| DELETE | `/admin/knowledge/{id}` | — | 删除文档与向量 |
| POST | `/admin/knowledge/reindex` | — | 重建全部索引 |

## 六、AI

| 方法 | 路径 | 请求体 | 响应 data |
| --- | --- | --- | --- |
| POST | `/ai/chat` | `{sessionId?, question}` | `{sessionId, answer, citations[], degraded, notice}` |
| POST | `/ai/agent/chat` | `{sessionId?, message}` | `{sessionId, answer, trace[], confirm?, degraded}` |
| POST | `/ai/agent/confirm` | `{token, approved}` | `{status, repairCode, repairId, message}` |
| GET | `/ai/sessions` | `?mode=RAG\|AGENT` | 会话列表 |
| GET | `/ai/sessions/{id}` | — | 会话消息 |
| GET | `/ai/sessions/{id}/trace` | — | Agent 工具调用轨迹 |
| GET | `/ai/health` | — | `{available:true/false}` |

`confirm` 对象结构：

```json
{
  "token": "9f2c...",
  "preview": "拟为「EQ-002 台式扫描电子显微镜」创建报修工单，故障描述：…",
  "actionType": "CREATE_REPAIR",
  "equipmentId": 2,
  "equipmentCode": "EQ-002",
  "equipmentName": "台式扫描电子显微镜",
  "description": "真空度上不去",
  "contact": "",
  "expiresAt": "2026-11-09 11:20:00"
}
```

## 七、内部工具（仅 AI 服务，需 `X-Internal-Token`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/internal/tools/equipments` | 设备查询（keyword） |
| GET | `/internal/tools/equipments/{id}` | 设备详情 |
| POST | `/internal/tools/repairs/prepare` | 校验建单参数并生成确认文案，**不写库** |

## 八、其他

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 后端健康检查 |
| GET | `/stats/overview` | 管理员全局大盘（设备数、全部待审核/已通过预约、全部待受理/处理中工单），仅 ADMIN |
| GET | `/stats/my-overview` | 当前登录用户个人工作台统计（我的预约与工单计数） |
