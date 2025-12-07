<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="sidebar">
      <div class="sidebar-header">
        <h3>{{ isCollapsed ? '' : '数据显示工具' }}</h3>
        <el-button 
          link 
          class="collapse-btn" 
          @click="toggleSidebar"
        >
          <el-icon v-if="isCollapsed"><Expand /></el-icon>
          <el-icon v-else><Fold /></el-icon>
        </el-button>
      </div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleMenuSelect"
        :collapse="isCollapsed"
      >
        <el-menu-item index="/map">
          <el-icon><MapLocation /></el-icon>
          <span>地图展示</span>
        </el-menu-item>

        <el-menu-item index="/comparison">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据比较</span>
        </el-menu-item>

        <el-menu-item index="/heatmap">
          <el-icon><DataAnalysis /></el-icon>
          <span>省份冷热点空间分析</span>
        </el-menu-item>

        <el-menu-item index="/population">
          <el-icon><DataAnalysis /></el-icon>
          <span>人口经济耦合数据</span>
        </el-menu-item>

        <el-menu-item index="/predict">
          <el-icon><DataAnalysis /></el-icon>
          <span>GDP预测</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区域 -->
    <div class="main-content" :style="{ marginLeft: sidebarMargin }">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MapLocation, DataAnalysis, Fold, Expand } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const isCollapsed = ref(false)

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 侧边栏宽度
const sidebarWidth = computed(() => isCollapsed.value ? '64px' : '250px')

// 主内容区域左边距
const sidebarMargin = computed(() => isCollapsed.value ? '64px' : '250px')

// 处理菜单选择
const handleMenuSelect = (index: string) => {
  router.push(index)
}

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.layout-container {
  display: flex;
  width: 100%;
  height: 100vh;
}

.sidebar {
  background-color: #fff;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  border-right: 2px solid #e8e8e8;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  transition: width 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  box-sizing: border-box;
}

.sidebar-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  transition: opacity 0.3s ease;
}

.collapse-btn {
  font-size: 18px;
  color: #666;
  padding: 8px;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  color: #409eff;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.sidebar-menu {
  border-right: none;
  height: calc(100vh - 80px);
  transition: all 0.3s ease;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 250px;
}

.main-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  transition: margin-left 0.3s ease;
  height: 100vh;
}

/* 折叠状态下菜单项样式 */
:deep(.el-menu--collapse) .el-menu-item span {
  display: none;
}

:deep(.el-menu--collapse) .el-submenu__title span {
  display: none;
}

:deep(.el-menu--collapse) .el-submenu__icon-arrow {
  display: none;
}
</style>