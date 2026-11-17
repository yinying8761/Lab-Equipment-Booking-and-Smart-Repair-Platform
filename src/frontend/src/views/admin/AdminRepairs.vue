<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">工单处理</h2>
        <div class="page-subtitle">受理工单、更新处理记录、填写结果并完成；无效或重复工单可关闭并说明原因。</div>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-select v-model="status" placeholder="全部状态" clearable style="width: 150px" @change="load(1)">
          <el-option label="待受理" value="PENDING" />
          <el-option label="处理中" value="PROCESSING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索工单号 / 描述" clearable style="width: 260px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="工单编号" width="170" />
        <el-table-column label="设备" min-width="200">
          <template #default="{ row }">
            <div>{{ row.equipmentName }}</div>
            <div class="muted mono">{{ row.equipmentCode }} · {{ row.laboratory }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="applicantName" label="提交人" width="90" />
        <el-table-column prop="description" label="故障描述" min-width="240" show-overflow-tooltip />
        <el-table-column label="来源" width="95">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source === 'AGENT' ? 'warning' : 'info'" effect="plain">
              {{ row.source === 'AGENT' ? '智能助手' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="repairStatusType[row.status]" size="small">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="150">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDrawer(row)">处理</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无工单" />
        </template>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="size" :current-page="page" @current-change="load" />
    </div>

    <el-drawer v-model="drawerVisible" title="工单处理" size="560px">
      <template v-if="current">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="工单编号">{{ current.code }}</el-descriptions-item>
          <el-descriptions-item label="设备">
            {{ current.equipmentCode }} {{ current.equipmentName }}（{{ current.laboratory }}）
          </el-descriptions-item>
          <el-descriptions-item label="提交人">{{ current.applicantName }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ current.contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="故障描述">{{ current.description }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="repairStatusType[current.status]" size="small">{{ current.statusLabel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="处理结果">{{ current.resolution || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="action-box">
          <el-input v-model="resolution" type="textarea" :rows="4" maxlength="1000" show-word-limit
                    placeholder="填写处理记录或最终处理结果，例如：已更换转子轴承并做动平衡校准" />

          <div class="action-buttons">
            <el-button v-if="current.status === 'PENDING'" type="primary" :loading="acting"
                       @click="accept">受理工单</el-button>
            <el-button v-if="current.status === 'PROCESSING'" :loading="acting" @click="saveProgress">
              保存处理记录
            </el-button>
            <el-button v-if="['PENDING', 'PROCESSING'].includes(current.status)" type="success"
                       :loading="acting" @click="complete">完成工单</el-button>
            <el-button v-if="['PENDING', 'PROCESSING'].includes(current.status)" type="danger" plain
                       :loading="acting" @click="close">关闭工单</el-button>
          </div>
        </div>

        <h4 class="panel-title" style="margin-top: 20px">处理轨迹</h4>
        <el-timeline>
          <el-timeline-item v-for="(log, index) in current.logs" :key="index"
                            :timestamp="formatDateTime(log.time)" placement="top">
            <div>{{ log.summary }}</div>
            <div class="muted" style="font-size: 12px">操作人：{{ log.operator || '-' }}</div>
          </el-timeline-item>
        </el-timeline>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { repairApi } from '../../api'
import { formatDateTime, repairStatusType } from '../../utils/format'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const status = ref('PENDING')
const keyword = ref('')
const loading = ref(false)

const drawerVisible = ref(false)
const current = ref(null)
const resolution = ref('')
const acting = ref(false)

async function load(target = page.value) {
  page.value = target
  loading.value = true
  try {
    const res = await repairApi.adminList({
      status: status.value || undefined, keyword: keyword.value || undefined,
      page: page.value, size
    })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function openDrawer(row) {
  const res = await repairApi.detail(row.id)
  current.value = res.data
  resolution.value = res.data.resolution || ''
  drawerVisible.value = true
}

async function refreshCurrent() {
  if (!current.value) return
  const res = await repairApi.detail(current.value.id)
  current.value = res.data
  resolution.value = res.data.resolution || ''
  load()
}

async function accept() {
  acting.value = true
  try {
    await repairApi.accept(current.value.id)
    ElMessage.success('已受理，状态更新为处理中')
    await refreshCurrent()
  } finally {
    acting.value = false
  }
}

async function saveProgress() {
  if (!resolution.value.trim()) {
    ElMessage.warning('请填写处理记录')
    return
  }
  acting.value = true
  try {
    await repairApi.progress(current.value.id, resolution.value)
    ElMessage.success('处理记录已保存')
    await refreshCurrent()
  } finally {
    acting.value = false
  }
}

async function complete() {
  if (!resolution.value.trim()) {
    ElMessage.warning('完成工单必须填写处理结果')
    return
  }
  acting.value = true
  try {
    await repairApi.complete(current.value.id, resolution.value)
    ElMessage.success('工单已完成')
    await refreshCurrent()
    drawerVisible.value = false
  } finally {
    acting.value = false
  }
}

async function close() {
  const { value } = await ElMessageBox.prompt('请填写关闭原因（如重复工单、信息不完整）', '关闭工单', {
    inputPattern: /\S+/,
    inputErrorMessage: '关闭原因不能为空',
    type: 'warning'
  })
  acting.value = true
  try {
    await repairApi.close(current.value.id, value)
    ElMessage.success('工单已关闭')
    await refreshCurrent()
    drawerVisible.value = false
  } finally {
    acting.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.action-box {
  margin-top: 18px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}
</style>
