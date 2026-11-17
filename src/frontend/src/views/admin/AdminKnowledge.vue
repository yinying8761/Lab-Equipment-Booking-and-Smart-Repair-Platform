<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2 class="page-title">知识库管理</h2>
        <div class="page-subtitle">
          支持 txt / md / pdf / docx，单文件不超过 10MB。上传后自动解析、切分并写入向量库，可重建索引。
        </div>
      </div>
      <div>
        <el-button :icon="Refresh" :loading="reindexing" @click="reindex">重建索引</el-button>
        <el-button type="primary" :icon="Upload" @click="uploadVisible = true">上传文档</el-button>
      </div>
    </div>

    <div class="panel">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="title" label="文档标题" min-width="220" />
        <el-table-column prop="sourceName" label="文件名" min-width="200" />
        <el-table-column prop="fileType" label="类型" width="90" />
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ (row.fileSize / 1024).toFixed(1) }} KB</template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tooltip v-if="row.status === 'FAILED'" :content="row.errorMessage || '处理失败'">
              <el-tag type="danger" size="small">{{ row.statusLabel }}</el-tag>
            </el-tooltip>
            <el-tag v-else :type="row.status === 'READY' ? 'success' : 'warning'" size="small">
              {{ row.statusLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunkCount" label="分片数" width="90" />
        <el-table-column label="上传时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="知识库为空，请先上传设备手册或操作规范" />
        </template>
      </el-table>
    </div>

    <el-dialog v-model="uploadVisible" title="上传知识文档" width="520px">
      <el-form label-width="80px">
        <el-form-item label="文档标题">
          <el-input v-model="title" placeholder="不填写则使用文件名" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload ref="uploadRef" drag :auto-upload="false" :limit="1" :show-file-list="true"
                     :on-change="onFileChange" :on-exceed="onExceed" accept=".txt,.md,.pdf,.docx">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处，或<em>点击选择</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 txt / md / pdf / docx，单个文件不超过 10MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传并索引</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Upload, UploadFilled } from '@element-plus/icons-vue'
import { knowledgeApi } from '../../api'
import { formatDateTime } from '../../utils/format'

const list = ref([])
const loading = ref(false)
const reindexing = ref(false)
const uploadVisible = ref(false)
const uploading = ref(false)
const title = ref('')
const file = ref(null)
const uploadRef = ref()

async function load() {
  loading.value = true
  try {
    const res = await knowledgeApi.list()
    list.value = res.data
  } finally {
    loading.value = false
  }
}

function onFileChange(uploadFile) {
  file.value = uploadFile.raw
}

function onExceed() {
  ElMessage.warning('每次只能上传一个文件')
}

async function submitUpload() {
  if (!file.value) {
    ElMessage.warning('请选择文件')
    return
  }
  const formData = new FormData()
  formData.append('file', file.value)
  if (title.value) formData.append('title', title.value)
  uploading.value = true
  try {
    const res = await knowledgeApi.upload(formData)
    ElMessage.success(`《${res.data.title}》已索引，共 ${res.data.chunkCount} 个分片`)
    uploadVisible.value = false
    title.value = ''
    file.value = null
    uploadRef.value?.clearFiles()
    load()
  } finally {
    uploading.value = false
  }
}

async function reindex() {
  reindexing.value = true
  try {
    const res = await knowledgeApi.reindex()
    ElMessage.success(`${res.data.message}（${res.data.chunks} 个分片）`)
    load()
  } finally {
    reindexing.value = false
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`删除《${row.title}》后，该文档将不再作为问答依据。`, '删除文档', { type: 'warning' })
  await knowledgeApi.remove(row.id)
  ElMessage.success('文档已删除')
  load()
}

onMounted(load)
</script>
