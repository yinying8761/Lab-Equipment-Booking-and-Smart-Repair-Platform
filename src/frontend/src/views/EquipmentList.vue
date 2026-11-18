<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">设备台账</h2>
        <div class="page-subtitle">共 {{ total }} 台设备，可按名称、编号、类别或实验室筛选。</div>
      </div>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input v-model="filters.keyword" placeholder="搜索名称 / 编号 / 实验室" clearable
                  style="width: 240px" @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="filters.category" placeholder="类别" clearable style="width: 150px" @change="load(1)">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="load(1)">
          <el-option label="可用" value="AVAILABLE" />
          <el-option label="维修中" value="MAINTENANCE" />
          <el-option label="停用" value="DISABLED" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
        <el-button :icon="Refresh" @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="编号" width="110" />
        <el-table-column prop="name" label="设备名称" min-width="180" />
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column prop="laboratory" label="所属实验室" min-width="150" />
        <el-table-column prop="location" label="位置" min-width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="equipmentStatusType[row.status]" effect="light" size="small">
              {{ row.statusLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" :icon="Calendar" @click="openSlots(row)">占用时段</el-button>
            <el-button link type="primary" :disabled="row.status !== 'AVAILABLE'" @click="openReserve(row)">
              预约
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="没有符合条件的设备" />
        </template>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="filters.size" :current-page="filters.page" @current-change="load" />
    </div>

    <el-drawer v-model="drawerVisible" title="设备详情" size="480px">
      <template v-if="detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="设备编号">{{ detail.code }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="类别">{{ detail.category }}</el-descriptions-item>
          <el-descriptions-item label="所属实验室">{{ detail.laboratory }}</el-descriptions-item>
          <el-descriptions-item label="位置">{{ detail.location || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="equipmentStatusType[detail.status]" size="small">{{ detail.statusLabel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="设备简介">{{ detail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="使用说明">{{ detail.usageNote || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="drawer-actions">
          <el-button type="primary" :disabled="detail.status !== 'AVAILABLE'" @click="openReserve(detail)">
            预约该设备
          </el-button>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="reserveVisible" title="提交设备预约" width="520px">
      <el-form ref="reserveFormRef" :model="reserveForm" :rules="reserveRules" label-width="88px">
        <el-form-item label="设备">
          <el-input :model-value="reserveEquipment.code + ' ' + reserveEquipment.name" disabled />
        </el-form-item>
        <el-form-item label="预约时段" prop="range">
          <el-date-picker v-model="reserveForm.range" type="datetimerange" style="width: 100%"
                          range-separator="至" start-placeholder="开始时间" end-placeholder="结束时间"
                          format="YYYY-MM-DD HH:mm" :disabled-date="disabledDate" :default-time="defaultTime" />
        </el-form-item>
        <el-form-item label="用途" prop="purpose">
          <el-input v-model="reserveForm.purpose" maxlength="200" show-word-limit
                    placeholder="例如：细胞样品离心分离" />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon
                  title="规则：时间粒度 30 分钟，单次 0.5~4 小时，需提前 30 分钟且最多提前 7 天。" />
      </el-form>
      <template #footer>
        <el-button @click="reserveVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReserve">提交预约</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="slotsVisible" width="620px"
               :title="`设备占用时段 · ${slotsEquipment.code || ''} ${slotsEquipment.name || ''}`">
      <div class="slot-toolbar">
        <el-date-picker v-model="slotsRange" type="daterange" range-separator="至"
                        start-placeholder="开始日期" end-placeholder="结束日期"
                        format="YYYY-MM-DD" :clearable="false" style="width: 280px" />
        <el-button type="primary" :icon="Search" :loading="slotsLoading" @click="loadSlots">查询</el-button>
      </div>

      <div v-if="slotsQuery.startText" class="slot-summary">
        查询区间 {{ slotsQuery.startText }} ~ {{ slotsQuery.endText }}，
        共 {{ slots.length }} 个已被预约的时段
      </div>

      <div v-loading="slotsLoading" class="slot-body">
        <div v-for="group in groupedSlots" :key="group.date" class="slot-day">
          <div class="slot-day-title">
            <span>{{ group.date }}</span>
            <span class="slot-day-count">{{ group.items.length }} 段占用</span>
          </div>
          <div class="slot-chips">
            <el-tag v-for="item in group.items" :key="item.id" type="danger" effect="light">
              {{ slotLabel(item) }}
            </el-tag>
          </div>
        </div>
        <el-empty v-if="!slotsLoading && !slots.length"
                  description="该时间范围内暂无已被预约的时段，可放心选择" :image-size="80" />
      </div>

      <div class="slot-hint">
        <el-icon><InfoFilled /></el-icon>
        <span>仅展示「已审核通过」的预约；待审核申请不占用时段。请避开上述时间段提交预约。</span>
      </div>

      <template #footer>
        <el-button @click="slotsVisible = false">关闭</el-button>
        <el-button type="primary" :disabled="slotsEquipment.status !== 'AVAILABLE'" @click="reserveFromSlots">
          预约该设备
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Calendar, InfoFilled } from '@element-plus/icons-vue'
import { equipmentApi, reservationApi } from '../api'
import { equipmentStatusType } from '../utils/format'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const filters = reactive({ keyword: '', category: '', status: '', page: 1, size: 10 })
const categories = ref([])

const drawerVisible = ref(false)
const detail = ref(null)

const reserveVisible = ref(false)
const submitting = ref(false)
const reserveFormRef = ref()
const reserveEquipment = ref({})
const defaultTime = [new Date(2000, 0, 1, 9, 0, 0), new Date(2000, 0, 1, 11, 0, 0)]
const reserveForm = reactive({ range: [], purpose: '' })
const reserveRules = {
  range: [{ required: true, message: '请选择预约时段', trigger: 'change' }],
  purpose: [{ required: true, message: '请填写用途', trigger: 'blur' }]
}

const slotsVisible = ref(false)
const slotsLoading = ref(false)
const slotsEquipment = ref({})
const slotsRange = ref([])
const slots = ref([])
const slotsQuery = reactive({ startText: '', endText: '' })

const groupedSlots = computed(() => {
  const map = new Map()
  for (const item of slots.value) {
    const day = String(item.startTime).slice(0, 10)
    if (!map.has(day)) map.set(day, [])
    map.get(day).push(item)
  }
  return [...map.entries()].map(([date, items]) => ({ date, items }))
})

function disabledDate(date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const limit = new Date(today)
  limit.setDate(limit.getDate() + 7)
  return date.getTime() < today.getTime() || date.getTime() > limit.getTime()
}

async function load(page = filters.page) {
  filters.page = page
  loading.value = true
  try {
    const res = await equipmentApi.list({ ...filters })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function reset() {
  filters.keyword = ''
  filters.category = ''
  filters.status = ''
  load(1)
}

async function openDetail(row) {
  const res = await equipmentApi.detail(row.id)
  detail.value = res.data
  drawerVisible.value = true
}

function openReserve(row) {
  reserveEquipment.value = row
  reserveForm.range = []
  reserveForm.purpose = ''
  reserveVisible.value = true
}

function dayText(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function openSlots(row) {
  slotsEquipment.value = row
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const weekLater = new Date(today)
  weekLater.setDate(weekLater.getDate() + 7)
  slotsRange.value = [today, weekLater]
  slots.value = []
  slotsQuery.startText = ''
  slotsQuery.endText = ''
  slotsVisible.value = true
  loadSlots()
}

async function loadSlots() {
  if (!slotsRange.value || slotsRange.value.length !== 2) {
    ElMessage.warning('请选择查询日期范围')
    return
  }
  slotsQuery.startText = dayText(slotsRange.value[0])
  slotsQuery.endText = dayText(slotsRange.value[1])
  slotsLoading.value = true
  try {
    const res = await reservationApi.reservedTime(slotsEquipment.value.id, {
      start: `${slotsQuery.startText} 00:00:00`,
      end: `${slotsQuery.endText} 23:59:59`
    })
    slots.value = res.data || []
  } finally {
    slotsLoading.value = false
  }
}

function slotLabel(item) {
  const start = String(item.startTime)
  const end = String(item.endTime)
  if (start.slice(0, 10) === end.slice(0, 10)) {
    return `${start.slice(11, 16)} - ${end.slice(11, 16)}`
  }
  return `${start.slice(5, 16)} - ${end.slice(5, 16)}`
}

function reserveFromSlots() {
  slotsVisible.value = false
  openReserve(slotsEquipment.value)
}

function roundUp(date) {
  const d = new Date(date)
  d.setSeconds(0, 0)
  const remainder = d.getMinutes() % 30
  if (remainder !== 0) {
    d.setMinutes(d.getMinutes() + (30 - remainder))
  }
  return d
}

function roundDown(date) {
  const d = new Date(date)
  d.setSeconds(0, 0)
  d.setMinutes(d.getMinutes() - (d.getMinutes() % 30))
  return d
}

function toText(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ` +
    `${pad(date.getHours())}:${pad(date.getMinutes())}:00`
}

async function submitReserve() {
  await reserveFormRef.value.validate()
  const [start, end] = reserveForm.range
  const realStart = roundUp(start)
  const realEnd = roundDown(end)
  if (realEnd <= realStart) {
    ElMessage.warning('扣除对齐误差后时段为空，请重新选择时间')
    return
  }
  submitting.value = true
  try {
    const res = await reservationApi.create({
      equipmentId: reserveEquipment.value.id,
      startTime: toText(realStart),
      endTime: toText(realEnd),
      purpose: reserveForm.purpose
    })
    ElMessage.success(`预约已提交：${res.data.code}，等待管理员审核`)
    reserveVisible.value = false
    router.push('/reservations')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await load(1)
  const res = await equipmentApi.list({ page: 1, size: 100 })
  categories.value = [...new Set(res.data.list.map((item) => item.category))]
})
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.drawer-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.slot-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slot-summary {
  margin-top: 14px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.slot-body {
  margin-top: 12px;
  min-height: 120px;
  max-height: 360px;
  overflow-y: auto;
}

.slot-day {
  padding: 10px 0;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}

.slot-day:last-child {
  border-bottom: none;
}

.slot-day-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.slot-day-count {
  font-weight: 400;
  color: var(--el-color-danger);
}

.slot-chips {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.slot-hint {
  margin-top: 12px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--el-fill-color-light);
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}
</style>
