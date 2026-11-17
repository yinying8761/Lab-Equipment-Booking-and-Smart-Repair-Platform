<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">设备管理</h2>
        <div class="page-subtitle">维护设备台账：新增、编辑与状态切换。设备编号唯一，停用后不能提交新预约。</div>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增设备</el-button>
    </div>

    <div class="panel">
      <div class="filter-bar">
        <el-input v-model="filters.keyword" placeholder="搜索名称 / 编号 / 实验室" clearable style="width: 240px"
                  @keyup.enter="load(1)" @clear="load(1)" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="load(1)">
          <el-option label="可用" value="AVAILABLE" />
          <el-option label="维修中" value="MAINTENANCE" />
          <el-option label="停用" value="DISABLED" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load(1)">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="code" label="编号" width="110" />
        <el-table-column prop="name" label="名称" min-width="170" />
        <el-table-column prop="category" label="类别" width="110" />
        <el-table-column prop="laboratory" label="实验室" min-width="150" />
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-select :model-value="row.status" size="small" style="width: 105px"
                       @change="(value) => changeStatus(row, value)">
              <el-option label="可用" value="AVAILABLE" />
              <el-option label="维修中" value="MAINTENANCE" />
              <el-option label="停用" value="DISABLED" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination class="pager" background layout="total, prev, pager, next" :total="total"
                     :page-size="filters.size" :current-page="filters.page" @current-change="load" />
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑设备' : '新增设备'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="设备编号" prop="code">
              <el-input v-model="form.code" placeholder="EQ-011" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备名称" prop="name">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类别" prop="category">
              <el-input v-model="form.category" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="可用" value="AVAILABLE" />
                <el-option label="维修中" value="MAINTENANCE" />
                <el-option label="停用" value="DISABLED" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实验室" prop="laboratory">
              <el-input v-model="form.laboratory" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="位置">
              <el-input v-model="form.location" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="设备简介">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="使用说明">
          <el-input v-model="form.usageNote" type="textarea" :rows="3" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { equipmentApi } from '../../api'
import { formatDateTime } from '../../utils/format'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const filters = reactive({ keyword: '', status: '', page: 1, size: 10 })

const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref()
const form = reactive({
  id: null, code: '', name: '', category: '', laboratory: '', location: '',
  status: 'AVAILABLE', description: '', usageNote: ''
})
const rules = {
  code: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  category: [{ required: true, message: '请输入类别', trigger: 'blur' }],
  laboratory: [{ required: true, message: '请输入实验室', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
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

function openCreate() {
  Object.assign(form, {
    id: null, code: '', name: '', category: '', laboratory: '', location: '',
    status: 'AVAILABLE', description: '', usageNote: ''
  })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(form, row)
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    const payload = {
      code: form.code, name: form.name, category: form.category, laboratory: form.laboratory,
      location: form.location, status: form.status, description: form.description, usageNote: form.usageNote
    }
    if (form.id) {
      await equipmentApi.update(form.id, payload)
      ElMessage.success('设备已更新')
    } else {
      await equipmentApi.create(payload)
      ElMessage.success('设备已新增')
    }
    dialogVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

async function changeStatus(row, status) {
  await equipmentApi.changeStatus(row.id, status)
  ElMessage.success('设备状态已更新')
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
