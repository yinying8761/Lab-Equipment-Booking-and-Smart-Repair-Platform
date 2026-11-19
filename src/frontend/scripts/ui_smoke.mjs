/**
 * 前端端到端 UI 冒烟 + 运行截图生成。
 *
 * 用法：
 *   node scripts/ui_smoke.mjs
 * 前置：后端 8080、AI 服务 8100、前端 5173 均已启动。
 * 产物：evidence/运行截图或录屏/*.png 与 ui_smoke_report.json
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../../..')
const SHOT_DIR = path.join(ROOT, 'evidence', '运行截图或录屏')
const REPORT = path.join(ROOT, 'evidence', '测试与构建', 'ui_smoke_report.json')

const CHROME = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
].find((p) => fs.existsSync(p))

const BASE = process.env.LAB_FRONTEND || 'http://127.0.0.1:5173'
// 直连后端用于准备测试数据（不经 Vite 代理，避免依赖前端进程状态）
const API_BASE = process.env.LAB_BACKEND || 'http://127.0.0.1:8080'
const results = []
const consoleErrors = []

function ok(name, passed, detail = '') {
  results.push({ name, passed, detail })
  console.log(`${passed ? '[PASS]' : '[FAIL]'} ${name} ${detail}`)
}

async function shot(page, name) {
  fs.mkdirSync(SHOT_DIR, { recursive: true })
  await page.screenshot({ path: path.join(SHOT_DIR, `${name}.png`), fullPage: false })
}

async function clickByText(page, selector, text) {
  const clicked = await page.evaluate((sel, target) => {
    const nodes = [...document.querySelectorAll(sel)]
    const node = nodes.find((n) => n.textContent.replace(/\s+/g, '').includes(target))
    if (!node) return false
    node.click()
    return true
  }, selector, text)
  if (!clicked) throw new Error(`未找到可点击元素：${selector} 含 "${text}"`)
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

async function waitText(page, text, timeout = 30000) {
  await page.waitForFunction(
    (target) => document.body.innerText.includes(target),
    { timeout },
    text
  )
}

async function scrollToLastAnswer(page) {
  await page.evaluate(() => {
    const rows = document.querySelectorAll('.message-row.assistant')
    const last = rows[rows.length - 1]
    if (last) last.scrollIntoView({ block: 'start' })
  })
  await sleep(400)
}

async function fillComposer(page, text) {
  await page.waitForSelector('textarea')
  await page.$eval('textarea', (el, value) => {
    el.value = value
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, text)
  const current = await page.$eval('textarea', (el) => el.value)
  if (current !== text) throw new Error('输入框内容未正确写入')
}

async function login(page, username, password) {
  await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle2' })
  await page.waitForSelector('input[placeholder="请输入用户名"]', { timeout: 20000 })
  await page.type('input[placeholder="请输入用户名"]', username)
  await page.type('input[placeholder="请输入密码"]', password)
  await clickByText(page, 'button', '登录')
  await page.waitForFunction(() => location.hash.includes('/dashboard'), { timeout: 20000 })
  await page.waitForSelector('.stat-card', { timeout: 20000 })
  await sleep(2600)
}

async function logout(page) {
  await page.evaluate(() => localStorage.clear())
  await page.goto(BASE + '/#/login', { waitUntil: 'domcontentloaded' })
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(600)
}

/**
 * 预约审核页默认筛选「待审核」。若反复运行测试把待审核数据消耗完，
 * 页面会正确地显示空状态，导致后续断言等不到表格行。
 * 这里先通过接口补一条待审核预约，保证脚本可重复执行。
 */
async function seedPendingReservation() {
  const api = `${API_BASE}/api`
  const login = await fetch(`${api}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'student02', password: 'Student@123' })
  }).then((r) => r.json())
  const token = login?.data?.token
  if (!token) throw new Error('预约数据准备失败：无法登录 student02')

  const pad = (n) => String(n).padStart(2, '0')
  const fmt = (d) =>
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ` +
    `${pad(d.getHours())}:${pad(d.getMinutes())}:00`

  // 选一台可用设备，预约「3 天后」的一个时段，避开已有预约冲突
  const equipments = await fetch(`${api}/equipments?status=AVAILABLE&page=1&size=50`, {
    headers: { Authorization: `Bearer ${token}` }
  }).then((r) => r.json())
  const equipment = equipments?.data?.list?.find((e) => e.status === 'AVAILABLE')
  if (!equipment) throw new Error('预约数据准备失败：没有可用设备')

  const start = new Date()
  start.setDate(start.getDate() + 3)
  start.setHours(10, 0, 0, 0)
  const end = new Date(start.getTime() + 60 * 60 * 1000)

  const created = await fetch(`${api}/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      equipmentId: equipment.id,
      startTime: fmt(start),
      endTime: fmt(end),
      purpose: 'UI 冒烟测试自动准备数据'
    })
  }).then((r) => r.json())

  if (created?.code !== 0) {
    // 时段被占用等可恢复情况：换一台设备再试一次
    const other = equipments?.data?.list?.find((e) => e.id !== equipment.id && e.status === 'AVAILABLE')
    if (!other) throw new Error(`预约数据准备失败：${created?.message || '未知原因'}`)
    const retry = await fetch(`${api}/reservations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        equipmentId: other.id,
        startTime: fmt(start),
        endTime: fmt(end),
        purpose: 'UI 冒烟测试自动准备数据'
      })
    }).then((r) => r.json())
    if (retry?.code !== 0) throw new Error(`预约数据准备失败：${retry?.message || '未知原因'}`)
    return retry.data.code
  }
  return created.data.code
}

async function main() {
  if (!CHROME) throw new Error('未找到 Chrome 或 Edge')
  fs.mkdirSync(SHOT_DIR, { recursive: true })
  fs.mkdirSync(path.dirname(REPORT), { recursive: true })

  const seeded = await seedPendingReservation().catch((err) => {
    console.log(`[WARN] ${err.message}`)
    return null
  })
  if (seeded) console.log(`[准备] 已补充待审核预约 ${seeded}`)

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--window-size=1560,960', '--font-render-hinting=none']
  })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 960 })

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => consoleErrors.push(`pageerror: ${err?.stack || err?.message || String(err)}`))

  try {
    // 1. 登录页
    await page.goto(`${BASE}/#/login`, { waitUntil: 'networkidle2' })
    await page.waitForSelector('input[placeholder="请输入用户名"]')
    await shot(page, '01-登录页')
    ok('登录页渲染', true)

    // 2. 普通用户登录
    await login(page, 'student01', 'Student@123')
    await shot(page, '02-工作台')
    ok('学生登录并进入工作台', true)

    // 3. 设备台账
    await page.goto(`${BASE}/#/equipments`, { waitUntil: 'networkidle2' })
    await page.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    const rows = await page.$$eval('.el-table__row', (els) => els.length)
    await shot(page, '03-设备台账')
    ok('设备列表加载', rows > 0, `行数=${rows}`)

    // 4. 设备详情抽屉
    await clickByText(page, '.el-table__row button', '详情')
    await page.waitForSelector('.el-drawer', { visible: true, timeout: 15000 })
    await sleep(500)
    await waitText(page, '使用说明')
    await shot(page, '04-设备详情')
    ok('设备详情抽屉', true)
    await page.keyboard.press('Escape')

    // 4.5 我的预约
    await page.goto(BASE + '/#/reservations', { waitUntil: 'networkidle2' })
    await page.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(page, '12-我的预约')
    ok('我的预约列表', true)

    // 5. 返回首页并进入智能助手（知识问答）
    await page.goto(`${BASE}/#/assistant`, { waitUntil: 'networkidle2' })
    await page.waitForSelector('textarea')
    await shot(page, '05-智能助手入口')
    await fillComposer(page, '离心机报 E07 怎么处理？')
    await clickByText(page, 'button', '发送')
    await waitText(page, '引用来源', 60000)
    await scrollToLastAnswer(page)
    await shot(page, '06-RAG问答与引用')
    const citationCount = await page.$$eval('.source-card', (els) => els.length)
    ok('RAG 问答返回引用', citationCount > 0, `引用=${citationCount} 条`)

    // 6. 证据不足问题
    await fillComposer(page, '食堂今天中午吃什么？')
    await clickByText(page, 'button', '发送')
    await waitText(page, '无法确认', 60000)
    await shot(page, '07-RAG证据不足')
    ok('RAG 证据不足提示', true)

    // 7. Agent 助手
    await clickByText(page, '.el-tabs__item', '智能助手')
    await page.waitForFunction(() => {
      const active = document.querySelector('.el-tabs__item.is-active')
      return active && active.textContent.includes('Agent')
    }, { timeout: 10000 })
    await sleep(600)
    await fillComposer(page, 'EQ-002 电镜真空度上不去，帮我报修')
    await clickByText(page, 'button', '发送')
    await page.waitForSelector('.confirm-card', { timeout: 60000 })
    await shot(page, '08-Agent待确认')
    const previewText = await page.$eval('.confirm-body', (el) => el.textContent.trim())
    ok('Agent 生成待确认预览', previewText.length > 0, previewText.slice(0, 40))

    // 展开工具轨迹
    await clickByText(page, '.el-collapse-item__header', '工具调用轨迹')
    await sleep(500)
    await shot(page, '09-Agent工具调用轨迹')
    ok('Agent 工具轨迹可见', true)

    // 8. 取消确认
    await clickByText(page, '.confirm-actions button', '取消')
    await waitText(page, '已取消', 30000)
    await shot(page, '10-Agent取消确认')
    ok('取消确认未建单', true)

    // 9. 再次发起并确认建单
    await fillComposer(page, 'EQ-003 紫外分光光度计读数一直漂移，帮我准备报修单')
    await clickByText(page, 'button', '发送')
    await page.waitForFunction(() => {
      const buttons = [...document.querySelectorAll('.confirm-actions button')]
      return buttons.some((b) => b.textContent.includes('确认提交'))
    }, { timeout: 90000 })
    await clickByText(page, '.confirm-actions button', '确认提交')
    await waitText(page, '已创建', 40000)
    await shot(page, '11-Agent确认后建单')
    ok('确认后创建真实工单', true)

    // 10. 我的报修
    await page.goto(`${BASE}/#/repairs`, { waitUntil: 'networkidle2' })
    await page.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(page, '12-我的报修')
    ok('我的报修列表可查 Agent 工单', true)

    // 11. 管理员登录（使用新的浏览器上下文，避免残留会话干扰）
    const adminPage = await browser.newPage()
    await adminPage.setViewport({ width: 1560, height: 960 })
    adminPage.on('pageerror', (err) =>
      consoleErrors.push(`admin pageerror: ${err?.stack || err?.message || String(err)}`))
    adminPage.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(`admin console: ${msg.text()}`)
    })
    await login(adminPage, 'admin', 'Admin@123')
    await shot(adminPage, '13-管理员工作台')

    await adminPage.goto(`${BASE}/#/admin/reservations`, { waitUntil: 'networkidle2' })
    await adminPage.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(adminPage, '14-预约审核')
    ok('管理员预约审核页', true)

    await adminPage.goto(`${BASE}/#/admin/repairs`, { waitUntil: 'networkidle2' })
    await adminPage.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(adminPage, '15-工单处理')
    ok('管理员工单处理页', true)

    await adminPage.goto(`${BASE}/#/admin/knowledge`, { waitUntil: 'networkidle2' })
    await adminPage.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(adminPage, '16-知识库管理')
    ok('管理员知识库页', true)

    await adminPage.goto(`${BASE}/#/admin/equipments`, { waitUntil: 'networkidle2' })
    await adminPage.waitForSelector('.el-table__row', { timeout: 20000 })
    await sleep(700)
    await shot(adminPage, '17-设备管理')
    ok('管理员设备管理页', true)
  } catch (err) {
    ok('UI 流程异常', false, err.message)
    await shot(page, '99-异常现场').catch(() => {})
  } finally {
    const passed = results.filter((r) => r.passed).length
    fs.writeFileSync(REPORT, JSON.stringify({
      generatedAt: new Date().toLocaleString('zh-CN'),
      base: BASE,
      total: results.length,
      passed,
      consoleErrors,
      results
    }, null, 2), 'utf-8')
    console.log(`\n== UI 检查 ${results.length} 项，通过 ${passed} 项；控制台错误 ${consoleErrors.length} 条 ==`)
    if (consoleErrors.length) console.log(consoleErrors.slice(0, 10).join('\n'))
    await browser.close()
    process.exit(passed === results.length && consoleErrors.length === 0 ? 0 : 1)
  }
}

main()








