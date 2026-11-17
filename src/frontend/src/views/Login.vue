<template>
  <div class="login-page">
    <div class="login-left">
      <div class="brand">
        <div class="brand-mark">LC</div>
        <span>LabCare</span>
      </div>
      <h1>实验室设备预约<br />与智能报修平台</h1>
      <p class="intro">
        设备台账查询、预约申请与审核、故障报修与进度跟踪，
        并接入 RAG 知识问答与智能助手，覆盖实验室设备管理的主要业务闭环。
      </p>
      <ul class="feature-list">
        <li><el-icon><Box /></el-icon> 设备台账：编号、位置、状态、使用说明一站式查询</li>
        <li><el-icon><Calendar /></el-icon> 预约管理：时间冲突校验，管理员审核留痕</li>
        <li><el-icon><Tools /></el-icon> 报修闭环：提交、受理、处理、完成全程可追踪</li>
        <li><el-icon><ChatDotRound /></el-icon> 智能能力：带来源引用的问答与确认后建单</li>
      </ul>
    </div>

    <div class="login-right">
      <el-card class="login-card" shadow="never">
        <h2>登录</h2>
        <p class="muted">使用演示账号进入系统</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" size="large" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" size="large" show-password
                      placeholder="请输入密码" :prefix-icon="Lock" @keyup.enter="submit" />
          </el-form-item>
          <el-button type="primary" size="large" class="submit" :loading="loading" @click="submit">
            登录
          </el-button>
        </el-form>

        <el-divider>演示账号</el-divider>
        <div class="demo-accounts">
          <div class="demo-account" @click="fill('student01', 'Student@123')">
            <span class="tag">学生</span>
            <span class="mono">student01 / Student@123</span>
          </div>
          <div class="demo-account" @click="fill('student02', 'Student@123')">
            <span class="tag">学生</span>
            <span class="mono">student02 / Student@123</span>
          </div>
          <div class="demo-account" @click="fill('admin', 'Admin@123')">
            <span class="tag admin">管理员</span>
            <span class="mono">admin / Admin@123</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function fill(username, password) {
  form.username = username
  form.password = password
}

async function submit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const user = await auth.login({ ...form })
    ElMessage.success(`欢迎，${user.displayName}`)
    router.push(route.query.redirect || '/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  min-height: 100vh;
}

.login-left {
  background: linear-gradient(150deg, #1f4e79 0%, #163a5a 60%, #0f2b44 100%);
  color: #fff;
  padding: 56px 64px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 40px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-left h1 {
  font-size: 34px;
  line-height: 1.45;
  margin: 0 0 18px;
  font-weight: 600;
}

.intro {
  color: #c5d6e6;
  line-height: 1.9;
  max-width: 520px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 28px 0 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #d6e3f0;
  padding: 8px 0;
  font-size: 14px;
}

.login-right {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f6f9;
  padding: 32px;
}

.login-card {
  width: 400px;
  border-radius: 14px;
  padding: 8px 8px 4px;
}

.login-card h2 {
  margin: 0 0 4px;
  color: var(--lab-primary);
}

.submit {
  width: 100%;
  margin-top: 4px;
}

.demo-accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.demo-account {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px dashed #d8e0ea;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.demo-account:hover {
  border-color: var(--lab-primary-light);
  background: #f7fafd;
}

.tag {
  background: #eaf2fb;
  color: #2f6fb2;
  border-radius: 4px;
  padding: 1px 8px;
  font-size: 12px;
}

.tag.admin {
  background: #fdecec;
  color: #c45656;
}
</style>
