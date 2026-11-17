<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的预约</h2>
        <div class="page-subtitle">提交预约后由管理员审核；审核前可自行取消，已通过的预约可查看审核意见。</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="$router.push('/equipments')">新建预约</el-button>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-select v-model="status" placeholder="全部状态" clearable style="width: 150px" @change="load(1)">
          <el-option label="待审核" value="PENDING" />
          <el-option label="已通过" value="APPROVED" />
          <el-option label="已驳回" value="REJECTED" />
          <el-option label="已取消" value="CANCELLED" />
          <el-option label="已完成" value="COMPLETED" />
        </el-select>
        <el-button :icon="Refresh" @click="load()">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="预约编号" width="170" />
        <el-table-column label="设备" min-width="200">
          <template #default="{ row }">
            <div>{{ row.equipmentName }}</div>
            <div class="muted mono">{{ row.equipmentCode }} · {{ row.laboratory }}</div>
          </template>
        </el-table-column>
        <el-table-column label="预约时段" min-width="200">
          <template #default="{ row }">
            {{ formatDateTime(row.startTime) }} ~ {{ formatDateTime(row.endTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="用途" min-width="140" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="reservationStatusType[row.status]" size="small">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button v-if="row.status === 'PENDING'" link type="danger" @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有预约记录，去设备台账发起一次预约吧" />
        </template>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="size" :current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="detailVisible" title="预约详情" width="560px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="预约编号">{{ current.code }}</el-descriptions-item>
        <el-descriptions-item label="设备">{{ current.equipmentCode }} {{ current.equipmentName }}</el-descriptions-item>
        <el-descriptions-item label="实验室">{{ current.laboratory }}</el-descriptions-item>
        <el-descriptions-item label="时段">
          {{ formatDateTime(current.startTime) }} ~ {{ formatDateTime(current.endTime) }}
        </el-descriptions-item>
        <el-descriptions-item label="用途">{{ current.purpose || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="reservationStatusType[current.status]" size="small">{{ current.statusLabel }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="审核人">{{ current.reviewerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核意见">{{ current.reviewComment || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ formatDateTime(current.reviewedAt) }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ formatDateTime(current.createdAt) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { reservationApi } from '../api'
import { formatDateTime, reservationStatusType } from '../utils/format'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const status = ref('')
const loading = ref(false)
const detailVisible = ref(false)
const current = ref(null)

async function load(target = page.value) {
  page.value = target
  loading.value = true
  try {
    const res = await reservationApi.mine({ status: status.value || undefined, page: page.value, size })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function openDetail(row) {
  current.value = row
  detailVisible.value = true
}

async function cancel(row) {
  await ElMessageBox.confirm(`确定取消预约 ${row.code} 吗？`, '取消预约', { type: 'warning' })
  await reservationApi.cancel(row.id)
  ElMessage.success('预约已取消')
  load()
}

onMounted(() => load(1))
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
