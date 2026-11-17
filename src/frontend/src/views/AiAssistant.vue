<template>
  <div class="page assistant-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">智能助手</h2>
        <div class="page-subtitle">
          知识问答基于设备手册检索并展示来源；智能助手会调用业务工具，创建工单前必须由你确认。
        </div>
      </div>
      <div class="header-actions">
        <el-tag v-if="degraded" type="warning" effect="plain" size="small">降级模式：检索真实，回答为原文摘要</el-tag>
        <el-button :icon="Plus" @click="startNew">新会话</el-button>
        <el-button :icon="Clock" @click="historyVisible = true">历史会话</el-button>
      </div>
    </div>

    <el-tabs v-model="mode" class="mode-tabs" @tab-change="onModeChange">
      <el-tab-pane label="知识问答（RAG）" name="RAG" />
      <el-tab-pane label="智能助手（Agent）" name="AGENT" />
    </el-tabs>

    <div class="chat-panel">
      <div ref="scrollRef" class="messages">
        <div v-if="!messages.length" class="welcome">
          <el-icon :size="40" color="#2f6fb2"><ChatDotRound /></el-icon>
          <h3>{{ mode === 'RAG' ? '向知识库提问' : '让助手帮你查设备或报修' }}</h3>
          <p class="muted">
            {{ mode === 'RAG'
              ? '回答只依据知识库中的设备手册与规范，并标注来源；资料不足时会明确说明。'
              : '助手会调用设备查询、报修预览工具；只有你确认后才会真正创建工单。' }}
          </p>
          <div class="examples">
            <el-button v-for="item in examples" :key="item" size="small" round @click="ask(item)">
              {{ item }}
            </el-button>
          </div>
        </div>

        <div v-for="(message, index) in messages" :key="index" class="message-row"
             :class="message.role">
          <div class="chat-bubble" :class="message.role">
            <div class="bubble-text">{{ message.content }}</div>

            <div v-if="message.degraded" class="degraded-note">
              <el-icon><Warning /></el-icon> {{ message.notice || '当前为降级模式' }}
            </div>

            <div v-if="message.citations && message.citations.length" class="citations">
              <div class="citation-title">引用来源</div>
              <div v-for="(citation, cIndex) in message.citations" :key="cIndex" class="source-card">
                <div class="source-head">
                  <strong>[{{ cIndex + 1 }}] 《{{ citation.title }}》</strong>
                  <span class="muted">第 {{ citation.chunkIndex + 1 }} 段 · 相关度 {{ (citation.score || 0).toFixed(2) }}</span>
                </div>
                <div class="source-snippet">{{ citation.snippet }}</div>
              </div>
            </div>

            <div v-if="message.trace && message.trace.length" class="trace">
              <el-collapse>
                <el-collapse-item :title="`工具调用轨迹（${message.trace.length} 步）`">
                  <div v-for="step in message.trace" :key="step.step" class="trace-item">
                    <el-tag size="small" :type="step.success ? 'success' : 'danger'" effect="plain">
                      {{ step.step }}. {{ step.tool }}
                    </el-tag>
                    <span class="trace-input">入参：{{ step.input }}</span>
                    <div>返回：{{ step.output }}</div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>

            <div v-if="message.confirm" class="confirm-card">
              <div class="confirm-head">待确认操作</div>
              <div class="confirm-body">{{ message.confirm.preview }}</div>
              <div v-if="message.confirmResult" class="confirm-result">
                <el-tag :type="message.confirmResult.status === 'CONFIRMED' ? 'success' : 'info'" size="small">
                  {{ message.confirmResult.status === 'CONFIRMED' ? '已创建' : '已取消' }}
                </el-tag>
                {{ message.confirmResult.message }}
                <el-button v-if="message.confirmResult.repairCode" link type="primary"
                           @click="$router.push('/repairs')">查看工单</el-button>
              </div>
              <div v-else class="confirm-actions">
                <el-button size="small" @click="confirmAction(message, false)">取消</el-button>
                <el-button size="small" type="primary" :loading="message.confirming"
                           @click="confirmAction(message, true)">确认提交</el-button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="sending" class="message-row assistant">
          <div class="chat-bubble assistant muted">正在检索并生成回答…</div>
        </div>
      </div>

      <div class="composer">
        <el-input v-model="input" type="textarea" :rows="3" resize="none"
                  :placeholder="mode === 'RAG' ? '例如：离心机报 E07 怎么处理？' : '例如：EQ-002 电镜真空度上不去，帮我报修'"
                  @keydown.enter.exact.prevent="ask()" />
        <div class="composer-actions">
          <span class="muted">Enter 发送 / Shift + Enter 换行</span>
          <el-button type="primary" :icon="Promotion" :loading="sending" @click="ask()">发送</el-button>
        </div>
      </div>
    </div>

    <el-drawer v-model="historyVisible" title="历史会话" size="420px">
      <el-empty v-if="!sessions.length" description="暂无历史会话" />
      <div v-for="session in sessions" :key="session.id" class="session-item"
           @click="loadSession(session)">
        <div class="session-title">{{ session.title }}</div>
        <div class="muted" style="font-size: 12px">{{ formatDateTime(session.updatedAt) }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Clock, Promotion, Warning } from '@element-plus/icons-vue'
import { aiApi } from '../api'
import { formatDateTime } from '../utils/format'

const mode = ref('RAG')
const messages = ref([])
const input = ref('')
const sending = ref(false)
const sessionId = ref(null)
const degraded = ref(false)
const sessions = ref([])
const historyVisible = ref(false)
const scrollRef = ref()

const examples = computed(() =>
  mode.value === 'RAG'
    ? ['离心机报 E07 怎么处理？', '紫外分光光度计开机要预热多久？', '生物安全柜使用前要做什么？', '食堂今天中午吃什么？']
    : ['查一下 EQ-001 的使用说明', 'EQ-002 电镜真空度上不去，帮我报修', 'EQ-003 读数一直漂移，帮我准备报修单']
)

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}

function startNew() {
  sessionId.value = null
  messages.value = []
  input.value = ''
}

async function onModeChange() {
  startNew()
  degraded.value = false
}

async function ask(text) {
  const question = (text || input.value).trim()
  if (!question || sending.value) return
  input.value = ''
  messages.value.push({ role: 'user', content: question })
  sending.value = true
  scrollToBottom()
  try {
    const payload = { sessionId: sessionId.value, [mode.value === 'RAG' ? 'question' : 'message']: question }
    const res = mode.value === 'RAG'
      ? await aiApi.chat(payload)
      : await aiApi.agentChat(payload)
    const data = res.data
    sessionId.value = data.sessionId
    if (data.degraded) degraded.value = true
    messages.value.push({
      role: 'assistant',
      content: data.answer,
      citations: data.citations || [],
      trace: data.trace || [],
      degraded: data.degraded,
      notice: data.notice,
      confirm: data.confirm || null,
      confirming: false,
      confirmResult: null
    })
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，本次请求失败。你可以稍后重试，或使用「我的报修」页面手动提交工单。',
      citations: [],
      trace: []
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

async function confirmAction(message, approved) {
  message.confirming = true
  try {
    const res = await aiApi.confirm({ token: message.confirm.token, approved })
    message.confirmResult = res.data
    if (res.data.status === 'CONFIRMED') {
      ElMessage.success(res.data.message)
    } else {
      ElMessage.info(res.data.message)
    }
  } finally {
    message.confirming = false
  }
}

async function loadSessions() {
  const res = await aiApi.sessions(mode.value)
  sessions.value = res.data
}

async function loadSession(session) {
  const res = await aiApi.sessionDetail(session.id)
  sessionId.value = session.id
  messages.value = res.data.messages.map((item) => ({
    role: item.role,
    content: item.content,
    citations: item.citations ? JSON.parse(item.citations) : [],
    degraded: item.degraded,
    trace: [],
    confirm: null,
    confirming: false,
    confirmResult: null
  }))
  historyVisible.value = false
  scrollToBottom()
}

onMounted(async () => {
  await loadSessions()
  try {
    const res = await aiApi.health()
    degraded.value = !res.data.available
  } catch (e) {
    degraded.value = true
  }
})
</script>

<style scoped>
.assistant-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 58px);
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.mode-tabs {
  margin-bottom: 8px;
}

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--lab-border);
  border-radius: 10px;
  overflow: hidden;
  min-height: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  background: #fafbfd;
}

.welcome {
  text-align: center;
  padding: 48px 16px;
}

.welcome h3 {
  margin: 12px 0 6px;
  color: var(--lab-primary);
}

.examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 18px;
}

.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.user {
  justify-content: flex-end;
}

.bubble-text {
  line-height: 1.75;
}

.degraded-note {
  margin-top: 8px;
  font-size: 12px;
  color: #b88230;
  background: #fdf6ec;
  border-radius: 6px;
  padding: 6px 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.citations {
  margin-top: 10px;
}

.citation-title {
  font-size: 12px;
  color: var(--lab-muted);
  margin-bottom: 4px;
}

.source-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.source-snippet {
  margin-top: 4px;
  color: #4a5563;
  line-height: 1.6;
}

.trace {
  margin-top: 8px;
}

.trace-input {
  margin-left: 8px;
  color: var(--lab-muted);
}

.confirm-card {
  margin-top: 12px;
  border: 1px solid #f0c78a;
  background: #fffaf2;
  border-radius: 8px;
  padding: 12px;
}

.confirm-head {
  font-weight: 600;
  color: #b88230;
  margin-bottom: 6px;
}

.confirm-body {
  line-height: 1.7;
}

.confirm-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.confirm-result {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.composer {
  border-top: 1px solid var(--lab-border);
  padding: 12px 16px;
  background: #fff;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.session-item {
  padding: 12px;
  border: 1px solid var(--lab-border);
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
}

.session-item:hover {
  border-color: var(--lab-primary-light);
  background: #f7fafd;
}

.session-title {
  font-weight: 600;
  margin-bottom: 4px;
}
</style>
