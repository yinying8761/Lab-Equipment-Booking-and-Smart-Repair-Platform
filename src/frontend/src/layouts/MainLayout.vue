<template>
  <el-container class="layout">
    <el-aside width="228px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">LC</div>
        <div>
          <div class="brand-title">LabCare</div>
          <div class="brand-sub">实验室设备预约与智能报修</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="menu" background-color="transparent"
               text-color="#c9d6e4" active-text-color="#ffffff">
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon><span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/equipments">
          <el-icon><Box /></el-icon><span>设备台账</span>
        </el-menu-item>
        <el-menu-item index="/reservations">
          <el-icon><Calendar /></el-icon><span>我的预约</span>
        </el-menu-item>
        <el-menu-item index="/repairs">
          <el-icon><Tools /></el-icon><span>我的报修</span>
        </el-menu-item>
        <el-menu-item index="/assistant">
          <el-icon><ChatDotRound /></el-icon><span>智能助手</span>
        </el-menu-item>

        <template v-if="auth.isAdmin">
          <div class="menu-group">管理功能</div>
          <el-menu-item index="/admin/equipments">
            <el-icon><Setting /></el-icon><span>设备管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/reservations">
            <el-icon><DocumentChecked /></el-icon><span>预约审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/repairs">
            <el-icon><Service /></el-icon><span>工单处理</span>
          </el-menu-item>
          <el-menu-item index="/admin/knowledge">
            <el-icon><Collection /></el-icon><span>知识库管理</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-title">{{ route.meta.title || '' }}</div>
        <div class="topbar-right">
          <el-tag :type="auth.isAdmin ? 'danger' : 'info'" effect="plain" size="small">
            {{ auth.user?.roleLabel || '普通用户' }}
          </el-tag>
          <el-dropdown @command="onCommand">
            <span class="user-chip">
              <el-avatar :size="28">{{ (auth.displayName || '访').slice(0, 1) }}</el-avatar>
              <span>{{ auth.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" disabled>{{ auth.user?.username }}</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

async function onCommand(command) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100%;
}

.sidebar {
  background: linear-gradient(180deg, #1f4e79 0%, #163a5a 100%);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 18px 14px;
  color: #fff;
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-sub {
  font-size: 11px;
  color: #a8c0d8;
  margin-top: 2px;
}

.menu {
  border-right: none;
  padding: 6px 8px 24px;
}

.menu :deep(.el-menu-item) {
  border-radius: 8px;
  margin: 2px 0;
  height: 44px;
}

.menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.16);
}

.menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1);
}

.menu-group {
  color: #7f9cba;
  font-size: 11px;
  letter-spacing: 2px;
  padding: 16px 14px 6px;
}

.topbar {
  background: #fff;
  border-bottom: 1px solid var(--lab-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 58px;
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--lab-primary);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--lab-text);
  font-size: 14px;
}

.content {
  padding: 0;
  overflow-y: auto;
}
</style>
