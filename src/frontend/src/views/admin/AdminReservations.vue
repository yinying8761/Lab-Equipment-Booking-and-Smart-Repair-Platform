<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">预约审核</h2>
        <div class="page-subtitle">
          批准前系统会再次校验时间冲突；驳回必须填写意见。待审核申请不占用时段，先批准者先占用。
        </div>
      </div>
    </div>

    <div class="panel">
      <el-tabs v-model="status" @tab-change="load(1)">
        <el-tab-pane label="待审核" name="PENDING" />
        <el-tab-pane label="已通过" name="APPROVED" />
        <el-tab-pane label="全部" name="" />
      </el-tabs>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="预约编号" width="170" />
        <el-table-column label="设备" min-width="190">
          <template #default="{ row }">
            <div>{{ row.equipmentName }}</div>
            <div class="muted mono">{{ row.equipmentCode }} · {{ row.laboratory }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="applicantName" label="申请人" width="100" />
        <el-table-column label="时段" min-width="200">
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
        <el-table-column label="提交时间" width="150">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'PENDING'" link type="primary" @click="openReview(row)">
              审核
            </el-button>
            <el-button v-if="row.status === 'APPROVED'" link type="success" @click="complete(row)">
              标记完成
            </el-button>
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="没有需要处理的预约" />
        </template>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="size" :current-page="page" @current-change="load" />
    </div>

    <el-dialog v-model="reviewVisible" title="审核预约" width="520px">
      <el-descriptions v-if="current" :column="1" border size="small">
        <el-descriptions-item label="预约编号">{{ current.code }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ current.applicantName }}</el-descriptions-item>
        <el-descriptions-item label="设备">
          {{ current.equipmentCode }} {{ current.equipmentName }}
        </el-descriptions-item>
        <el-descriptions-item label="时段">
          {{ formatDateTime(current.startTime) }} ~ {{ formatDateTime(current.endTime) }}
        </el-descriptions-item>
        <el-descriptions-item label="用途">{{ current.purpose || '-' }}</el-descriptions-item>
      </el-descriptions>
      <el-form label-width="80px" style="margin-top: 16px">
        <el-form-item label="审核结果">
          <el-radio-group v-model="reviewForm.approve">
            <el-radio :value="true">通过</el-radio>
            <el-radio :value="false">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核意见">
          <el-input v-model="reviewForm.comment" type="textarea" :rows="3" maxlength="200" show-word-limit
                    :placeholder="reviewForm.approve ? '可填写使用注意事项' : '驳回时必须填写原因'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReview">提交审核</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="预约详情" width="520px">
      <el-descriptions v-if="current" :column="1" border size="small">
        <el-descriptions-item label="预约编号">{{ current.code }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ current.applicantName }}</el-descriptions-item>
        <el-descriptions-item label="设备">
          {{ current.equipmentCode }} {{ current.equipmentName }}（{{ current.laboratory }}）
        </el-descriptions-item>
        <el-descriptions-item label="时段">
          {{ formatDateTime(current.startTime) }} ~ {{ formatDateTime(current.endTime) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">{{ current.statusLabel }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ current.reviewerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核意见">{{ current.reviewComment || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ formatDateTime(current.reviewedAt) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reservationApi } from '../../api'
import { formatDateTime, reservationStatusType } from '../../utils/format'

const status = ref('PENDING')
const list = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const loading = ref(false)

const reviewVisible = ref(false)
const detailVisible = ref(false)
const submitting = ref(false)
const current = ref(null)
const reviewForm = reactive({ approve: true, comment: '' })

async function load(target = page.value) {
  page.value = target
  loading.value = true
  try {
    const res = await reservationApi.adminList({
      status: status.value || undefined, page: page.value, size
    })
    list.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function openReview(row) {
  current.value = row
  reviewForm.approve = true
  reviewForm.comment = '同意，请按操作规程使用。'
  reviewVisible.value = true
}

function openDetail(row) {
  current.value = row
  detailVisible.value = true
}

async function submitReview() {
  if (!reviewForm.approve && !reviewForm.comment.trim()) {
    ElMessage.warning('驳回时必须填写审核意见')
    return
  }
  submitting.value = true
  try {
    await reservationApi.review(current.value.id, { ...reviewForm })
    ElMessage.success('审核已完成')
    reviewVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

async function complete(row) {
  await ElMessageBox.confirm(`确认将预约 ${row.code} 标记为已完成？`, '标记完成', { type: 'info' })
  await reservationApi.complete(row.id)
  ElMessage.success('已标记为完成')
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
