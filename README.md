# LabCare · 实验室设备预约与智能报修平台

第 11 组课程设计项目。面向高校实验室师生与管理员，提供设备台账、预约申请与审核、故障报修与进度跟踪，
并集成 **RAG 知识问答** 与 **LangChain Agent 智能助手**（工具调用 + 用户确认后建单）。

- 技术栈：Vue 3 + Vite + Element Plus ｜ Spring Boot 3.5 + JPA + MySQL 8 ｜ Python FastAPI + LangChain + Chroma
- 演示方式：三个服务本地启动，浏览器访问 `http://localhost:5173`
- 文档：需求见 `第11组-实验室设备预约与智能报修平台-需求文档.docx`

---

## 一、目录结构

```
.
├── README.md                      # 本文件：启动、账号、AI 能力与验收说明
├── 课设文档-实验室设备预约与智能报修平台.docx   # 课程设计文档（需求/概要/详细设计/调试/总结）
├── 答辩PPT-实验室设备预约与智能报修平台.pptx    # 答辩演示
├── 测试结果.xlsx                  # 用例、结果与证据位置
├── 成员任务表.xlsx                # 成员分工与成果位置
├── 一键启动.bat                   # 双击启动三个服务并打开浏览器
├── 停止服务.bat                   # 双击停止三个服务
├── 初始化数据库.bat               # 双击重建数据库与种子数据
├── src/
│   ├── frontend/                  # Vue3 前端（Vite + Element Plus）
│   ├── backend/                   # Spring Boot 业务后端（鉴权、设备、预约、报修、知识库、AI 网关）
│   ├── ai-service/                # LangChain AI 服务
│   │   ├── app/rag/               # RAG 管道：解析、切分、向量化、混合检索、生成
│   │   └── app/agent/             # Agent：工具定义、调用循环、降级编排
│   ├── rag/README.md              # 指向 src/ai-service/app/rag（对应提交清单 src/rag/）
│   └── agent/README.md            # 指向 src/ai-service/app/agent（对应提交清单 src/agent/）
├── db/init.sql                    # 数据库初始化脚本（建库建表 + 种子数据）
├── config/
│   ├── local.env.example          # 本地配置模板（复制为 local.env 后填写）
│   └── ai-service.env.example     # AI 服务配置模板
├── data/
│   ├── 知识库/                    # RAG 语料：设备手册、安全规范、故障指南
│   └── 测试数据/                  # 验收用输入样例
├── scripts/                       # 一键启动脚本（PowerShell）
├── tests/api_smoke.py             # 验收场景自动化脚本（AT-01 ~ AT-11）
├── tests/ai_down_check.py         # AI 服务不可用时的降级验证
├── tools/                         # 文档与报表生成脚本（docx / xlsx / pptx）
├── docs/                          # 课设文档源文件、接口说明、演示脚本
├── evidence/                      # 运行截图、Agent 轨迹、RAG 验证、测试输出
└── 个人材料/                      # 每位成员的个人报告与工作证据
```

> 需求文档中 `src/rag/`、`src/agent/` 要求"若独立成模块则单独提交"。本项目把两者放在
> `src/ai-service/app/rag/` 与 `src/ai-service/app/agent/`，作为同一个 AI 服务交付，便于一键启动。

---

## 二、依赖与版本

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| JDK | 21 | 后端编译与运行（`JAVA_HOME` 指向 JDK 21） |
| Maven | 3.9+ | 后端构建 |
| Node.js | 18+（验证 24.15） | 前端构建 |
| Python | 3.11+（验证 3.14.4） | AI 服务 |
| MySQL | 8.0+ | 业务数据库 |

Python 依赖见 `src/ai-service/requirements.txt`：`langchain`、`langchain-openai`、`chromadb`、
`scikit-learn`、`jieba`、`rank-bm25`、`pypdf`、`python-docx`、`fastapi`、`uvicorn`。

```bash
pip install -r src/ai-service/requirements.txt
```

---

## 三、启动步骤

### 1. 配置

```powershell
Copy-Item config/local.env.example config/local.env
notepad config/local.env          # 填写 MySQL 密码；如需真实大模型，填写 LAB_LLM_API_KEY
```

`config/local.env` 只存在于本机，已在 `.gitignore` 中排除，提交包内不含任何真实密钥。

### 2. 初始化数据库

```powershell
mysql -u root -p --default-character-set=utf8mb4 < db/init.sql
```

脚本会创建 `labcare` 库、全部业务表与演示种子数据（3 个账号、10 台设备、预约与工单样例）。

### 3. 启动三个服务

**方式 A：双击脚本（推荐，无需命令行）**

| 脚本 | 作用 |
| --- | --- |
| `一键启动.bat` | 检查环境与配置 → 启动 AI 服务(8100)、后端(8080)、前端(5173) → 自动打开浏览器 |
| `停止服务.bat` | 停止三个服务（按窗口标题，兜底按端口） |
| `初始化数据库.bat` | 重建 `labcare` 库并写入种子数据（会清空已有数据，需输入 Y 确认） |

首次运行只需：双击 `初始化数据库.bat` → 双击 `一键启动.bat`。

`一键启动.bat` 会依次校验 `config/local.env`、Java（要求 21+，优先使用 `JAVA_HOME`）、
Node、Python、MySQL 连通性；若缺少前端依赖或后端 jar 会自动安装/构建；启动后自动打开
<http://localhost:5173>。三个服务各自在独立窗口运行，排错时直接看对应窗口的输出。

> 脚本文件使用 GBK 编码保存（Windows 中文控制台默认代码页 936），用记事本直接编辑即可，
> 不要另存为 UTF-8，否则中文提示会乱码。

**方式 B：PowerShell 分别启动**

```powershell
.\scripts\start-all.ps1
```

或分别启动：

```powershell
.\scripts\start-ai.ps1         # AI 服务   http://127.0.0.1:8100
.\scripts\start-backend.ps1    # 业务后端  http://127.0.0.1:8080/api
.\scripts\start-frontend.ps1   # 前端      http://localhost:5173
```

浏览器打开 **http://localhost:5173**。前端通过 Vite 代理把 `/api` 转发到 8080，无需额外配置跨域。

### 4. 演示账号

| 账号 | 密码 | 角色 | 用途 |
| --- | --- | --- | --- |
| `student01` | `Student@123` | 普通用户 | 查设备、预约、报修、AI 问答与助手（张同学） |
| `student02` | `Student@123` | 普通用户 | 越权测试与预约冲突测试（李同学） |
| `admin` | `Admin@123` | 管理员 | 设备维护、预约审核、工单处理、知识库管理（王老师） |

所有姓名、联系方式、设备数据均为虚构演示数据。

---

## 四、功能清单与验收对应

| 模块 | 功能 | 对应需求 |
| --- | --- | --- |
| 账号与权限 | 登录/登出、JWT 鉴权、后端接口级角色校验、数据归属校验 | FR-01~03 |
| 设备台账 | 按名称/编号/实验室筛选、分页、详情、使用说明 | FR-04~05 |
| 设备管理 | 新增、编辑、状态切换（可用/维修中/停用）、编号唯一 | FR-06 |
| 预约 | 提交（30 分钟粒度、提前 30 分钟~7 天、单次 ≤4 小时）、本人取消、审核前不占时段 | FR-07~09 |
| 预约审核 | 批准/驳回（必填意见）、批准时二次冲突校验、结束后标记完成 | FR-08、FR-10~11 |
| 报修 | 提交、本人列表与详情、处理轨迹 | FR-12~13、FR-15 |
| 工单处理 | 受理、更新处理记录、完成、关闭（非法状态跳转返回 409） | FR-14~15 |
| 知识库 | 上传 txt/md/pdf/docx（≤10MB）、删除、重建索引、分片入 MySQL | FR-16~17 |
| RAG 问答 | 带来源引用的回答、证据不足明确提示、会话上下文 | FR-18~19 |
| Agent | 查询设备、准备报修、确认后真实建单、执行轨迹留痕 | FR-20~23 |

---

## 五、AI 能力清单与测试输入

### 1. RAG 知识问答（`/ai/chat`）

- 语料：`data/知识库/` 下 3 篇文档（离心机使用手册、实验室安全操作规范、常见故障处理指南），共 16 个分片。
- 检索：Chroma 持久化向量库（字符 n-gram 哈希向量）+ BM25 词法重排的混合检索，Top-4。
- 生成：DeepSeek（OpenAI 兼容接口，当前模型 `deepseek-flash`）依据检索片段作答，强制标注 `[1][2]` 来源；资料不足时明确说明。
- **未配置 API Key 时自动降级**：检索与来源仍然真实，回答改为原文摘要，界面明确标注"降级模式"。

测试输入（可直接在"智能助手 → 知识问答"中输入）：

| 类型 | 输入 | 预期 |
| --- | --- | --- |
| 命中文档 | 离心机报 E07 怎么处理？ | 回答真空/制冷超时排查步骤，引用《高速冷冻离心机使用手册》 |
| 命中文档 | 紫外分光光度计开机要预热多久？ | 回答 20 分钟，引用对应段落 |
| 交叉文档 | 生物安全柜使用前要做什么？ | 引用安全规范与故障指南 |
| 证据不足 | 食堂今天中午吃什么？ | 明确"现有资料无法确认"，不编造，无引用 |

### 2. Agent 智能助手（`/ai/agent/chat`）

- 工具白名单：`search_equipment`（查设备）、`get_equipment`（查详情）、`prepare_repair`（生成报修预览）。
- 写操作安全：`prepare_repair` 只返回预览；用户点击"确认提交"后，由 **Spring Boot 后端** 以当前登录身份创建工单，
  Agent 无法直接写库；确认令牌一次性、10 分钟过期、重复确认不重复建单。
- 执行轨迹写入 `agent_run` 表，界面可展开查看每一步工具入参与返回。

测试输入：

| 类型 | 输入 | 预期 |
| --- | --- | --- |
| 查设备 | 查一下 EQ-001 的使用说明 | 调用 `search_equipment`/`get_equipment`，返回真实台账信息 |
| 准备报修 | EQ-002 电镜真空度上不去，帮我报修 | 调用 `prepare_repair`，返回确认卡片，**此时无工单** |
| 取消确认 | 点击"取消" | 工单数不变（可现场核对"我的报修"） |
| 确认建单 | 点击"确认提交" | 返回真实工单号，`我的报修` 与管理员工单列表均可查到，来源标记为"智能助手" |

---

## 六、数据库与关键规则

- 表：`app_user`、`equipment`、`reservation`、`repair_ticket`、`operation_log`、`knowledge_document`、
  `knowledge_chunk`、`chat_session`、`chat_message`、`agent_run`、`pending_action`。
- 预约冲突：提交时只与"已通过"预约比对；待审核不占用时段；管理员批准时通过设备行锁串行化并二次校验。
- 预约时间规则：30 分钟粒度、至少提前 30 分钟、最多提前 7 天、单次 0.5~4 小时（可在 `application.yml` 调整）。
- 报修状态机：`PENDING → PROCESSING → COMPLETED`，`PENDING/PROCESSING → CLOSED`；非法跳转返回 409。
- 密码使用 BCrypt 摘要存储；JWT 使用 HS256，默认 12 小时过期。

---

## 七、自动化验收

```powershell
$env:PYTHONIOENCODING='utf-8'

# 1. 接口级验收（AT-01 ~ AT-11，26 项）
python tests/api_smoke.py

# 2. 降级演练（先停止 8100 端口的 AI 服务）
python tests/ai_down_check.py

# 3. 浏览器端到端（后端、AI、前端均需启动）
cd src/frontend; node scripts/ui_smoke.mjs

# 4. 重新导出 RAG / Agent 证据
python tools/export_evidence.py
```

结果写入 `evidence/测试与构建/`（`api_smoke_report.json`、`ai_degradation_report.json`、`ui_smoke_report.json`），
截图写入 `evidence/运行截图或录屏/`，可直接对应 `测试结果.xlsx`。

## 八、交付物生成

成员与班级信息统一维护在 `docs/team.json`（唯一数据源），改它之后重建即可：

```powershell
# 一次性替换班级与三人学号，并自动重建 课设文档 / 成员任务表 / 答辩 PPT
python tools/apply_member_info.py --class 软件2201班 `
    --ids "郑颖浩=20220101,常辰=20220102,赵佳伟=20220103"

# 也可单独重建某一项
python tools/build_course_doc.py     # docs/课设文档.md -> 课设文档 DOCX（含截图）
python tools/build_deliverables.py   # 测试报告 -> 测试结果.xlsx 与 成员任务表.xlsx
python tools/build_ppt.py            # 答辩 PPT
python tools/check_deliverables.py   # 检查三份文档的结构完整性
```

---

## 九、常见问题

| 现象 | 处理 |
| --- | --- |
| 后端启动报 `Access denied for user` | 检查 `config/local.env` 中的 `LAB_DB_PASSWORD` 是否为本机 MySQL 密码 |
| 页面提示"AI 服务暂不可用" | 确认 8100 端口已启动；未配置 Key 时功能仍可用（降级模式） |
| 问答回答"现有资料无法确认" | 知识库未建索引：管理员 → 知识库管理 → 重建索引 |
| 修改了知识库文件 | 管理员 → 知识库管理 → 重建索引，或重新上传该文档 |
| 预约提示"与已有预约冲突" | 该时段已有"已通过"预约，系统按先批准先占用处理 |
| npm 安装依赖卡住 | 本机 `.npmrc` 中的代理已失效：`npm install --userconfig=<空配置> --registry=https://registry.npmmirror.com` |

---

## 十、安全说明

- 仓库与提交包中**不含任何真实 API Key**：模型密钥只通过 `config/local.env` 或环境变量注入。
- 所有数据为虚构演示数据；联系方式为 `1380000xxxx` 形式的占位号码。
- AI 服务与业务后端之间使用 `X-Internal-Token` 服务间令牌，且内部接口只提供查询与建单前校验。

