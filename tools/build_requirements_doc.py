from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION

OUT = r'F:\2026.11.2Project\第11组-实验室设备预约与智能报修平台-需求文档.docx'

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(0.75)
sec.bottom_margin = Inches(0.7)
sec.left_margin = Inches(0.82)
sec.right_margin = Inches(0.82)

# Set CJK fonts for document styles.
def set_font(style, name='宋体', size=10.5, bold=None, color=None):
    style.font.name = name
    style._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color:
        style.font.color.rgb = RGBColor(*color)

set_font(doc.styles['Normal'], '宋体', 10.5)
doc.styles['Normal'].paragraph_format.space_after = Pt(5)
doc.styles['Normal'].paragraph_format.line_spacing = 1.25
set_font(doc.styles['Title'], '黑体', 25, True, (31, 78, 121))
set_font(doc.styles['Heading 1'], '黑体', 16, True, (31, 78, 121))
set_font(doc.styles['Heading 2'], '黑体', 12.5, True, (46, 116, 181))
set_font(doc.styles['Heading 3'], '黑体', 11, True, (64, 64, 64))

# Header/footer
header = sec.header.paragraphs[0]
header.text = '实验室设备预约与智能报修平台｜需求规格说明书'
header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
for r in header.runs:
    r.font.name = '宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体'); r.font.size = Pt(8); r.font.color.rgb = RGBColor(120,120,120)
footer = sec.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = footer.add_run('第11组  ·  课程设计文档  ·  2026')
r.font.name = '宋体'; r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体'); r.font.size = Pt(8); r.font.color.rgb = RGBColor(120,120,120)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def set_cell_text(cell, text, bold=False, color=None, size=9.2):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(str(text))
    run.bold = bold
    run.font.name = '宋体'; run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体'); run.font.size = Pt(size)
    if color: run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for i, h in enumerate(headers):
        set_cell_text(t.rows[0].cells[i], h, True, (255,255,255), 9)
        shade(t.rows[0].cells[i], '1F4E79')
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], value, False, None, 8.8)
    if widths:
        for row in t.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t

def para(text='', boldlead=None):
    p = doc.add_paragraph()
    if boldlead and text.startswith(boldlead):
        r = p.add_run(boldlead); r.bold = True
        p.add_run(text[len(boldlead):])
    else:
        p.add_run(text)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2')
    p.paragraph_format.space_after = Pt(2)
    p.add_run(text)
    return p

def numbered(text):
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.space_after = Pt(2)
    p.add_run(text)
    return p

# Cover
p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(70); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('课程设计需求文档'); r.bold = True; r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体'); r.font.size=Pt(17); r.font.color.rgb=RGBColor(91,155,213)
p = doc.add_paragraph(style='Title'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(15)
p.add_run('实验室设备预约与\n智能报修平台')
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before = Pt(20)
r=p.add_run('需求规格说明书'); r.font.name='黑体'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'黑体'); r.font.size=Pt(16); r.bold=True
for _ in range(3): doc.add_paragraph('')
meta = doc.add_table(rows=4, cols=2); meta.style='Table Grid'; meta.alignment=WD_TABLE_ALIGNMENT.CENTER
for i,(a,b) in enumerate([
    ('项目组别','第11组'),
    ('文档版本','V1.0（初稿）'),
    ('编制日期','2026年11月9日'),
    ('建议技术栈','Spring Boot、MySQL、LangChain；Web前端框架待定'),
]):
    set_cell_text(meta.rows[i].cells[0],a,True,size=10); shade(meta.rows[i].cells[0],'D9EAF7')
    set_cell_text(meta.rows[i].cells[1],b,size=10)
doc.add_paragraph('')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run('用于课程设计范围确认与后续开发、测试、验收'); r.font.size=Pt(9); r.font.color.rgb=RGBColor(110,110,110)
doc.add_page_break()

# Document control
doc.add_heading('文档信息', level=1)
table(['项目','说明'], [
    ('文档目的','描述系统的目标用户、业务范围、功能需求、AI能力边界和验收标准，作为后续概要设计、实现和测试的依据。'),
    ('项目定位','面向高校实验室的轻量级设备预约与故障报修业务系统，AI用于设备知识问答和辅助创建报修单。'),
    ('阅读对象','课程教师、项目组成员、测试与验收人员。'),
    ('范围约定','本版为课程项目需求初稿；账号体系、页面框架、模型服务和部署环境可在设计阶段根据课程条件调整。'),
])
doc.add_heading('目录', level=1)
for item in ['1. 项目概述','2. 用户角色与业务流程','3. 功能需求','4. 数据需求','5. AI能力需求与边界','6. 非功能需求','7. 验收标准与测试场景','8. 技术与部署约束','9. 范围外事项与待确认问题']:
    para(item)

# 1
doc.add_heading('1. 项目概述', level=1)
doc.add_heading('1.1 项目背景', level=2)
para('实验室设备的预约、使用和故障报修通常分散在纸质登记、即时通讯或人工沟通中，容易出现设备信息难查、预约状态不清、故障处理进度不透明、设备资料查找耗时等问题。本项目拟实现一个面向实验室师生与管理员的轻量级 Web 系统，将设备信息、预约申请、报修处理及知识问答集中管理。')
doc.add_heading('1.2 项目目标', level=2)
for x in [
    '提供可查询的实验室设备台账，展示设备基本信息、所在实验室、可用状态及操作说明。',
    '支持师生提交设备预约申请并跟踪审核结果，管理员可以审核、处理或关闭预约。',
    '支持师生提交故障报修并查看处理进度，管理员可以受理、更新状态并填写处理结果。',
    '基于设备说明书和常见故障资料提供带来源依据的 RAG 问答。',
    '通过 LangChain Agent 调用受控业务工具，辅助查询设备并在用户确认后创建报修工单。',
    '形成可现场演示、可重复测试、便于教师核验的前后端与数据库业务闭环。',
]: bullet(x)
doc.add_heading('1.3 产品范围', level=2)
para('本项目以设备台账、预约和报修为核心业务，以知识库问答和有限工具调用作为 AI 增强能力。目标是完成一个小规模、可运行的课程原型，不建设面向真实高校生产环境的综合实验室管理平台。')
table(['范围内（本期）','范围外（本期不承诺）'], [
    ('账号登录与角色权限；设备查询和管理；预约申请及审核；报修提交、处理及进度查询；知识文档管理、检索问答、引用展示；Agent 查询设备及确认后建单。','真实校园统一身份认证；设备物联网/传感器接入；自动排课和复杂资源调度；财务结算、采购、库存；移动端原生 App；生产级多租户、灾备及高可用。'),
])

# 2
doc.add_heading('2. 用户角色与业务流程', level=1)
doc.add_heading('2.1 用户角色', level=2)
table(['角色','主要职责','权限范围'], [
    ('学生/教师（普通用户）','查询设备、提交预约、提交报修、查看本人申请与工单、使用知识问答和智能助手。','仅访问公开设备信息及本人业务记录；不可审核或修改他人记录。'),
    ('实验室管理员/维修人员','维护设备信息；审核预约；受理报修、更新处理进度并填写处理结果；维护知识库资料。','可管理被授权实验室的设备及业务记录；管理知识文档。课程原型可合并管理员与维修人员角色。'),
    ('系统管理员（可与实验室管理员合并）','管理演示账号、角色和基础配置。','拥有系统管理权限；关键管理操作应有记录。'),
])
para('权限实现原则：前端页面控制仅用于界面展示，所有数据权限和操作权限必须由后端接口再次校验。')
doc.add_heading('2.2 核心业务流程', level=2)
doc.add_heading('2.2.1 设备预约流程', level=3)
for x in ['普通用户登录并查看设备详情及可预约信息。','选择预约起止时间并提交申请；系统校验时间有效、设备可预约。','管理员审核申请并填写审核意见；通过或驳回后记录状态和时间。','用户查看审核结果；预约结束后管理员可将记录标记为已完成，必要时允许用户在审核前取消。']:
    numbered(x)
para('冲突规则：申请提交时检查时间范围合法性及已通过预约；管理员最终批准时再次检查冲突，避免并发申请造成同一设备在重叠时段被重复批准。待审核申请是否互相占用时段，课程原型默认不占用，管理员批准时按先批准先占用处理。')
doc.add_heading('2.2.2 故障报修流程', level=3)
for x in ['普通用户选择设备，填写故障描述和联系方式（演示数据可使用虚构信息）后提交报修。','系统生成唯一工单编号，初始状态为“待受理”，保存提交人、设备、描述和创建时间。','管理员受理工单后更新为“处理中”，可填写处理备注；完成后更新为“已完成”并记录处理结果。','用户在本人报修列表查看状态、处理记录和时间；管理员可对无效或重复工单标记为“已关闭”并说明原因。']:
    numbered(x)
doc.add_heading('2.2.3 AI问答与智能建单流程', level=3)
for x in ['用户在问答界面输入设备使用或故障问题，系统检索知识库相关片段并生成回答。','回答展示可追溯的资料名称及片段来源；证据不足时提示未能从现有资料确认，并建议联系管理员。','用户可请求智能助手查询设备信息或准备报修内容。','Agent 展示拟创建工单的设备与故障描述，须经用户明确确认后才调用建单工具；成功后返回真实工单编号及可打开的工单记录。']:
    numbered(x)

# 3
doc.add_heading('3. 功能需求', level=1)
para('优先级说明：P0 为课程验收必需；P1 为时间允许时实现；P2 为可选增强。')
doc.add_heading('3.1 账号、登录与权限', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-01','用户使用演示账号登录并退出；错误账号或密码应显示明确但不泄露敏感信息的提示。','P0','正确账号可进入系统，错误凭据无法登录。'),
    ('FR-02','系统至少区分普通用户与管理员；管理员页面/API仅对管理员开放。','P0','普通用户直接访问管理接口会被拒绝，不能通过修改请求读取他人业务记录。'),
    ('FR-03','普通用户只能查看、修改或取消本人允许操作的记录；关键写操作由后端校验身份和状态。','P0','使用两个普通账号交叉访问，不能查看或变更对方记录。'),
])
doc.add_heading('3.2 设备信息管理', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-04','普通用户可分页或列表查看设备，按名称、编号、类别或实验室进行基本筛选。','P0','搜索条件生效；无匹配结果时显示空状态。'),
    ('FR-05','设备详情至少包含设备编号、名称、类别、所属实验室、位置、状态、简介和可用说明。','P0','列表与详情字段一致，缺失字段有合理展示。'),
    ('FR-06','管理员可新增、编辑、停用设备；设备编号唯一，必填信息校验。','P0','重复编号被拒绝；停用设备不能提交新预约。'),
])
doc.add_heading('3.3 预约管理', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-07','用户提交设备及起止时间，系统验证必填项、开始时间早于结束时间且预约时间符合当前系统规则。','P0','非法时间或缺失设备时不创建记录，并给出提示。'),
    ('FR-08','系统检测已批准预约的时间冲突；管理员审核通过时再次检测冲突。','P0','重叠申请不能被同时批准；无冲突申请可正常通过。'),
    ('FR-09','用户查看本人预约列表、详情和审核状态；审核前可取消本人申请。','P0','状态变化能在列表和详情中同步体现；不允许越权取消。'),
    ('FR-10','管理员查看预约申请并通过或驳回，必须保存审核人、审核时间及意见。','P0','审核后状态、意见和操作记录可查询。'),
    ('FR-11','管理员可将已通过且结束的预约标记为已完成。','P1','状态转换符合规则，重复完成操作得到安全提示。'),
])
doc.add_heading('3.4 报修工单管理', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-12','用户提交设备报修，至少包含设备、故障描述；系统生成唯一工单编号和创建时间。','P0','成功后可在本人报修列表查到，详情数据与提交一致。'),
    ('FR-13','用户查看本人报修工单及状态、提交描述、处理结果和时间记录。','P0','用户不可查看其他用户的工单。'),
    ('FR-14','管理员可受理、更新处理中状态、填写处理备注/结果并完成或关闭工单。','P0','非法状态跳转被拒绝，正常流转有记录。'),
    ('FR-15','工单详情展示状态变更时间及操作者；至少保留创建、受理和完成/关闭记录。','P1','处理轨迹可供演示和验收核对。'),
])
doc.add_heading('3.5 知识库与RAG问答', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-16','管理员上传或录入设备说明书、操作规范和常见故障资料；支持课程项目可实现的常用文本格式。','P0','成功后显示文档名称及处理状态；不支持格式给出提示。'),
    ('FR-17','系统对文档进行解析、切分、索引，并支持重新构建或删除知识条目。','P0','新增资料可参与后续检索；删除资料后不应继续作为有效来源。'),
    ('FR-18','用户以自然语言提问，系统基于检索到的内容生成回答，并展示资料来源名称；条件允许时展示页码/片段。','P0','答案与测试语料相关，来源可定位；检索不到时明确说明证据不足。'),
    ('FR-19','系统保留基础问答会话上下文，支持用户连续追问；新会话可重新开始。','P1','连续问题能利用本会话上下文，切换会话不混淆历史。'),
])
doc.add_heading('3.6 LangChain Agent智能助手', level=2)
table(['编号','需求','优先级','验收要点'], [
    ('FR-20','Agent至少提供“查询设备信息”和“创建报修工单”两个业务工具；查询结果来自真实业务接口/数据库。','P0','工具调用结果与设备台账、工单记录一致，不是写死文本。'),
    ('FR-21','Agent创建报修工单前，必须向用户展示待提交信息并获得明确确认；未经确认不得写入。','P0','用户拒绝/取消时不产生工单；确认后只创建一次并返回编号。'),
    ('FR-22','Agent调用失败、参数缺失、设备无法识别或模型不可用时，应提示失败并提供手动报修入口。','P0','失败不产生伪成功提示，业务系统仍可手动完成报修。'),
    ('FR-23','记录必要的Agent执行事件，包括会话、工具名称、输入摘要、调用结果/错误及时间，供调试和演示使用。','P1','不记录密钥；日志不暴露不必要的个人信息。'),
])
doc.add_heading('3.7 管理与基础体验', level=2)
for x in ['普通用户可从首页进入设备、预约、报修和AI问答模块。','管理员具有设备管理、预约审核、工单处理和知识库管理入口。','对加载中、空列表、操作成功、输入错误、权限不足和服务异常提供清楚提示。','关键表单支持取消、二次确认或防重复提交，避免误操作和重复建单。']:
    bullet(x)

# 4
doc.add_heading('4. 数据需求', level=1)
doc.add_heading('4.1 核心数据实体', level=2)
table(['实体','主要字段（建议）','说明'], [
    ('用户 User','id、用户名、密码摘要、显示名、角色、状态、创建时间','密码不得明文存储；课程演示使用虚构账号。'),
    ('设备 Equipment','id、设备编号、名称、类别、实验室、位置、状态、简介、说明','设备编号唯一；状态至少包含可用、维修中、停用。'),
    ('预约 Reservation','id、预约编号、设备id、用户id、开始时间、结束时间、用途、状态、审核人、审核意见、时间戳','保存申请和审核结果；需校验时间冲突和状态转换。'),
    ('报修单 RepairTicket','id、工单编号、设备id、提交用户id、故障描述、状态、处理人、处理结果、创建/更新时间','工单编号唯一；状态至少待受理、处理中、已完成、已关闭。'),
    ('操作记录 OperationLog','id、操作者、对象类型及id、动作、摘要、时间','重点记录审核、状态变更和Agent建单等操作。'),
    ('知识文档 KnowledgeDocument','id、标题、来源说明、文件类型、处理状态、上传时间','关联解析后的文本分片及索引；保留来源信息用于引用。'),
    ('问答/Agent会话（可简化）','会话id、用户id、消息摘要、工具调用事件、时间','按需要实现；禁止保存API密钥等机密信息。'),
])
doc.add_heading('4.2 数据规则', level=2)
for x in ['所有业务记录具有唯一主键和创建/更新时间；关键状态变化保留操作者和时间。','设备、预约、报修之间使用明确关联；删除设备时若存在业务记录，应采用停用或限制删除，避免历史记录失联。','预约、报修均关联创建用户；用户查询个人记录必须由后端按当前登录身份过滤。','使用测试用虚构姓名、联系方式和设备数据；提交材料不包含真实API密钥或未经授权的个人信息。']:
    bullet(x)

# 5
doc.add_heading('5. AI能力需求与边界', level=1)
doc.add_heading('5.1 RAG知识问答', level=2)
para('知识库建议先准备少量、来源清晰的模拟或公开授权资料，例如设备使用说明、实验室安全规则和常见故障处理手册。系统应展示回答依据，避免把大模型生成文本误认为官方维修结论。新加入文档后应能重新处理并参与检索，以便现场验证。')
doc.add_heading('5.2 Agent工具调用', level=2)
para('Agent负责理解用户意图、收集必要参数并调用有限业务工具；Spring Boot业务后端负责身份验证、权限校验、业务规则和数据持久化。Agent不得绕过业务接口直接访问MySQL。写入操作必须经过用户确认；工具调用失败不得伪造成功结果。')
doc.add_heading('5.3 安全与可靠性边界', level=2)
for x in ['AI回答仅作为设备资料查询和报修辅助，不代替实验室安全规程、专业维修判断或管理员审批。','对于涉及人身安全、危险操作或资料无依据的问题，提示停止操作并联系实验室管理员，不生成未经证实的操作步骤。','AI服务不可用时，设备、预约和手动报修等基础业务仍应可以使用。','密钥通过本地环境变量或未提交的配置文件管理，提交仓库仅包含不含真实密钥的配置模板。']:
    bullet(x)

# 6
doc.add_heading('6. 非功能需求', level=1)
table(['类别','需求'], [
    ('易用性','页面采用清晰导航；关键业务操作步骤简明；表单字段有名称、校验和错误提示；普通用户能快速找到设备、预约和报修入口。'),
    ('性能目标','在课程演示环境及小规模测试数据下，常规查询/写入接口目标响应时间不超过3秒（不含模型推理和文件解析）；AI问答设置合理超时并提示等待或失败。'),
    ('安全性','后端统一鉴权与授权；使用参数化数据库访问；限制上传文件类型和大小；日志不写入密钥；敏感操作校验角色及记录归属。'),
    ('可靠性','业务写操作失败时返回明确结果，不产生部分成功；重复提交具备防重机制或幂等保护；AI服务异常不影响非AI模块。'),
    ('可维护性','前后端分层；业务接口和AI工具边界清晰；提供配置模板、数据库初始化脚本、README和演示数据。'),
    ('兼容性','面向常见桌面浏览器完成课程演示；具体浏览器版本以项目测试环境为准。'),
    ('可测试性','核心业务应能通过演示账号和初始化数据重复验证；重要需求有对应测试用例及截图/日志证据。'),
])

# 7
doc.add_heading('7. 验收标准与测试场景', level=1)
para('以下场景为最低验收集合。测试结果应据实记录；涉及RAG和Agent的测试使用现场新输入，不以预置固定答案代替真实检索或工具调用。')
table(['编号','测试场景','预期结果'], [
    ('AT-01','普通用户登录后查询设备并打开详情。','设备列表、筛选和详情正常，信息来自业务数据库。'),
    ('AT-02','提交一条合法预约，管理员审核通过，用户查看状态。','申请成功保存；管理员可审核；用户看到状态、审核意见。'),
    ('AT-03','提交非法时间范围或与已批准预约重叠的申请，再尝试审核冲突申请。','非法时间被拒绝；冲突预约不能同时批准并有明确提示。'),
    ('AT-04','用户提交报修，管理员受理、更新处理结果并完成。','生成唯一工单号；工单状态及处理信息在双方页面一致。'),
    ('AT-05','使用普通账号请求访问他人预约/工单或管理员接口。','后端拒绝越权访问，不泄露他人数据。'),
    ('AT-06','基于知识库现有手册提问，并查看引用来源。','回答能显示相关资料名称/片段；来源可定位。'),
    ('AT-07','对知识库没有依据的问题提问。','系统说明当前资料无法确认，不编造确定结论。'),
    ('AT-08','上传一份新测试文档后提问其独有内容。','完成索引后可检索到新文档，并展示正确来源。'),
    ('AT-09','让Agent查询设备并准备报修，但选择取消确认。','展示待提交内容；取消后无新工单。'),
    ('AT-10','确认Agent创建报修工单，再到报修列表核验。','返回真实工单编号；数据库及页面均可查到同一条记录。'),
    ('AT-11','模拟模型/API不可用或工具调用异常。','提示服务异常或改用手动报修；不显示虚假的成功结果。'),
])
doc.add_heading('7.1 课程交付核验', level=2)
for x in ['演示环境可按README启动前端、Spring Boot后端、MySQL及LangChain AI服务/接口。','提供数据库初始化脚本或明确初始化步骤和测试账号；账号及样例数据均为虚构。','源码、文档、演示版本一致；提供核心业务运行证据、RAG引用验证、Agent工具调用记录和测试结果。','仓库和压缩包不包含真实API密钥、真实个人隐私数据或无关数据。']:
    bullet(x)

# 8
doc.add_heading('8. 技术与部署约束', level=1)
table(['部分','建议方案/约束'], [
    ('Web前端','实现浏览器端用户界面；具体框架由小组后续确定。'),
    ('业务后端','Spring Boot提供登录鉴权、设备/预约/工单管理、数据校验和REST接口。'),
    ('数据库','MySQL保存用户、设备、预约、报修及必要操作记录；提交初始化SQL或迁移说明。'),
    ('AI能力','LangChain实现文档解析/检索问答和Agent编排；通过受控服务接口调用Spring Boot业务工具。具体模型和向量存储方案在设计阶段依据课程环境确定。'),
    ('服务边界','AI组件不直接读写业务数据库；业务权限和事务规则由Spring Boot后端执行。模型配置与密钥放在环境变量或本地配置中。'),
    ('运行部署','课程演示环境优先采用易启动方案；README应列出运行依赖、启动顺序、配置项和常见故障处理。'),
])

# 9
doc.add_heading('9. 范围外事项与待确认问题', level=1)
doc.add_heading('9.1 明确不纳入本期的功能', level=2)
for x in ['真实设备传感器数据、自动故障诊断、远程控制设备。','复杂实验室排班、跨校区资源调度、预约收费、采购和库存管理。','短信/邮件等外部通知集成；如有时间可用站内状态提示替代。','生产环境等级的数据治理、灾备、监控和大规模并发能力。']:
    bullet(x)
doc.add_heading('9.2 后续需由小组确认的实现细节', level=2)
for x in ['Web前端具体框架及页面视觉方案。','模型服务/API和向量检索存储方案，以及是否需要额外服务。','预约时段粒度、预约提前量和是否需要管理员审核等细则。','设备文档的支持格式、单文件大小和索引重建方式。','是否将管理员与维修人员合并为一个演示角色。']:
    bullet(x)
para('在上述细节确认前，需求按本文件给出的课程项目默认规则执行；若后续调整，应同步更新需求、设计、测试用例和演示材料。')

# Save and verify by reopening.
doc.save(OUT)
check = Document(OUT)
all_text = '\n'.join(p.text for p in check.paragraphs)
normalized_text = all_text.replace('\n', '').replace(' ', '')
assert '实验室设备预约与智能报修平台' in normalized_text
assert 'Agent工具调用' in normalized_text
assert '验收标准与测试场景' in normalized_text
assert len(check.tables) >= 8
print(f'SAVED {OUT}')
print(f'PARAGRAPHS {len(check.paragraphs)} TABLES {len(check.tables)}')
print('KEY CONTENT VERIFIED')
