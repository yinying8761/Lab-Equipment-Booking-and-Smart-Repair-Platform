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
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
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
</style>
