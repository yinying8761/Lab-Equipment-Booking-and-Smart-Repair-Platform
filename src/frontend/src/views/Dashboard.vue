<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">工作台</h2>
        <div class="page-subtitle">欢迎回来，{{ auth.displayName }}。这里是实验室设备与报修业务的概览。</div>
      </div>
      <el-tag v-if="aiDegraded" type="warning" effect="plain">AI 服务：降级模式</el-tag>
      <el-tag v-else-if="aiAvailable" type="success" effect="plain">AI 服务：在线</el-tag>
      <el-tag v-else type="info" effect="plain">AI 服务：未连接</el-tag>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">设备总数</div>
        <div class="value">{{ stats.equipmentTotal ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">待审核预约</div>
        <div class="value">{{ stats.reservationPending ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">已通过预约</div>
        <div class="value">{{ stats.reservationApproved ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">待受理工单</div>
        <div class="value">{{ stats.repairPending ?? '-' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">处理中工单</div>
        <div class="value">{{ stats.repairProcessing ?? '-' }}</div>
      </div>
    </div>

    <div class="columns">
      <div class="panel">
        <h3 class="panel-title">快捷入口</h3>
        <div class="quick-grid">
          <div v-for="item in quickLinks" :key="item.path" class="quick-card" @click="$router.push(item.path)">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
            <div class="quick-title">{{ item.title }}</div>
            <div class="quick-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>

      <div class="panel">
        <h3 class="panel-title">答辩演示路径</h3>
        <el-steps direction="vertical" :active="0" finish-status="success" class="steps">
          <el-step title="设备台账" description="普通用户查看设备列表与详情（AT-01）" />
          <el-step title="预约闭环" description="提交预约 → 管理员审核 → 用户查看结果（AT-02/03）" />
          <el-step title="知识问答" description="提问设备手册问题并展示引用；再问语料外问题（AT-06/07）" />
          <el-step title="智能建单" description="Agent 查询设备 → 取消确认验证未建单 → 确认后建单（AT-09/10）" />
          <el-step title="工单处理" description="管理员受理并完成，用户查看进度（AT-04）" />
          <el-step title="越权校验" description="普通用户访问管理接口被拒绝（AT-05）" />
        </el-steps>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { aiApi, statsApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const stats = reactive({})
const aiAvailable = ref(false)
const aiDegraded = ref(false)

const quickLinks = [
  { title: '设备台账', desc: '查询设备状态与使用说明', path: '/equipments', icon: 'Box' },
  { title: '我的预约', desc: '提交预约、查看审核结果', path: '/reservations', icon: 'Calendar' },
  { title: '我的报修', desc: '提交报修、跟踪处理进度', path: '/repairs', icon: 'Tools' },
  { title: '智能助手', desc: '知识问答与确认后建单', path: '/assistant', icon: 'ChatDotRound' }
]

onMounted(async () => {
  try {
    const res = await statsApi.overview()
    Object.assign(stats, res.data)
  } catch (e) {
    /* 已由拦截器提示 */
  }
  try {
    const res = await aiApi.health()
    aiAvailable.value = res.data.available
    aiDegraded.value = false
  } catch (e) {
    aiAvailable.value = false
  }
})
</script>

<style scoped>
.columns {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-card {
  border: 1px solid var(--lab-border);
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.18s;
  color: var(--lab-primary);
}

.quick-card:hover {
  border-color: var(--lab-primary-light);
  box-shadow: 0 6px 18px rgba(31, 78, 121, 0.08);
  transform: translateY(-1px);
}

.quick-title {
  font-weight: 600;
  margin: 10px 0 4px;
  color: var(--lab-text);
}

.quick-desc {
  font-size: 12px;
  color: var(--lab-muted);
}

.steps {
  height: 300px;
}
</style>
