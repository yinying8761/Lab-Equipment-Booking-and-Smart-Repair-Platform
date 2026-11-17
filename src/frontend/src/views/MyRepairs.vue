<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的报修</h2>
        <div class="page-subtitle">提交故障报修并跟踪处理进度；绿色表示已完成，灰色表示已关闭。</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">提交报修</el-button>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-select v-model="status" placeholder="全部状态" clearable style="width: 150px" @change="load(1)">
          <el-option label="待受理" value="PENDING" />
          <el-option label="处理中" value="PROCESSING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已关闭" value="CLOSED" />
        </el-select>
        <el-button :icon="Refresh" @click="load()">刷新</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="工单编号" width="170" />
        <el-table-column label="设备" min-width="200">
          <template #default="{ row }">
            <div>{{ row.equipmentName }}</div>
            <div class="muted mono">{{ row.equipmentCode }} · {{ row.laboratory }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="故障描述" min-width="240" show-overflow-tooltip />
        <el-table-column label="来源" width="90">
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
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有报修记录" />
        </template>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="size" :current-page="page" @current-change="load" />
    </div>

    <el-drawer v-model="detailVisible" title="工单详情" size="520px">
      <template v-if="current">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="工单编号">{{ current.code }}</el-descriptions-item>
          <el-descriptions-item label="设备">
            {{ current.equipmentCode }} {{ current.equipmentName }}
          </el-descriptions-item>
          <el-descriptions-item label="故障描述">{{ current.description }}</el-descriptions-item>
          <el-descriptions-item label="联系方式">{{ current.contact || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="repairStatusType[current.status]" size="small">{{ current.statusLabel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="受理人">{{ current.handlerName || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理结果">{{ current.resolution || '-' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDateTime(current.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDateTime(current.completedAt) }}</el-descriptions-item>
        </el-descriptions>

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

    <el-dialog v-model="createVisible" title="提交故障报修" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="设备" prop="equipmentId">
          <el-select v-model="form.equipmentId" filterable placeholder="请选择设备" style="width: 100%">
            <el-option v-for="item in options" :key="item.id" :label="`${item.code} ${item.name}`"
                       :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="故障描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" maxlength="1000" show-word-limit
                    placeholder="请描述故障现象、发生时间以及是否影响使用" />
        </el-form-item>
        <el-form-item label="联系方式" prop="contact">
          <el-input v-model="form.contact" maxlength="50" placeholder="演示用虚构联系方式，如 13800000001" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">提交报修</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { equipmentApi, repairApi } from '../api'
import { formatDateTime, repairStatusType } from '../utils/format'

const list = ref([])
const total = ref(0)
const page = ref(1)
const size = 10
const status = ref('')
const loading = ref(false)
const detailVisible = ref(false)
const current = ref(null)

const createVisible = ref(false)
const submitting = ref(false)
const formRef = ref()
const options = ref([])
const form = reactive({ equipmentId: null, description: '', contact: '' })
const rules = {
  equipmentId: [{ required: true, message: '请选择设备', trigger: 'change' }],
  description: [{ required: true, message: '请填写故障描述', trigger: 'blur' },
    { min: 5, message: '请至少填写 5 个字', trigger: 'blur' }]
}

async function load(target = page.value) {
  page.value = target
  loading.value = true
  try {
    const res = await repairApi.mine({ status: status.value || undefined, page: page.value, size })
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

async function openCreate() {
  form.equipmentId = null
  form.description = ''
  form.contact = ''
  createVisible.value = true
  if (!options.value.length) {
    const res = await equipmentApi.options()
    options.value = res.data
  }
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    const res = await repairApi.create({ ...form })
    ElMessage.success(`报修已提交，工单号 ${res.data.code}`)
    createVisible.value = false
    await load(1)
    openDetail(res.data)
  } finally {
    submitting.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
