# Agent 模块位置说明

课程提交清单中的 `src/agent/`（智能体编排、提示词与工具定义）在本项目中作为**独立 AI 服务的一个子模块**实现，
源码位于：

```
src/ai-service/app/agent/
├── runner.py        # tool-calling 循环、提示词、规则化降级编排、待确认提案
└── tools.py         # 工具定义（search_equipment / get_equipment / prepare_repair）与后端调用
```

提示词常量 `AGENT_PROMPT` 在 `runner.py` 中；工具 JSON Schema 在 `tools.py` 的 `TOOL_SPECS` 中。

写操作的落库不在本模块：Agent 只能生成"待确认提案"，用户确认后由 Spring Boot 的
`AiService.confirm()` 以当前登录用户身份调用 `RepairService.create()` 写入，确认令牌保存在
`pending_action` 表（一次性、10 分钟过期）。执行轨迹写入 `agent_run` 表，可通过
`GET /ai/sessions/{id}/trace` 查询。

运行方式与验收输入见项目根目录 `README.md` 第五节。
