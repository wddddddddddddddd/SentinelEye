<template>
    <div class="w-64 bg-white shadow-lg flex flex-col">
        <div class="p-6 border-b">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center">
                    <i class="fas fa-shield-alt text-white text-xl"></i>
                </div>
                <h1 class="text-xl font-bold text-gray-800">反馈监控系统</h1>
            </div>
        </div>

        <div class="flex-1 py-4">
            <nav>
                <ul>
                    <li v-for="item in navItems" :key="item.id">
                        <router-link :to="item.path" :class="[
                            'nav-item flex items-center py-3 px-6 text-gray-600 hover:text-blue-600 hover:bg-blue-50 transition-colors',
                            { 'active': isActive(item.path) }
                        ]">
                            <i :class="[item.icon, 'w-6 mr-3 text-center']"></i>
                            <span>{{ item.label }}</span>
                        </router-link>
                    </li>
                </ul>
            </nav>
        </div>

        <div class="p-4 border-t text-center text-sm text-gray-500">
            <p>安全监控系统 v1.0</p>
        </div>
    </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
    name: 'Sidebar',
    setup() {
        const route = useRoute()

        const navItems = ref([
            { id: 'dashboard', label: '监控仪表盘', icon: 'fas fa-tachometer-alt', path: '/dashboard' },
            { id: 'analytics', label: '数据分析', icon: 'fas fa-chart-bar', path: '/analytics' },
            { id: 'keywords', label: '关键词管理', icon: 'fas fa-key', path: '/keywords' },
            { id: 'notifications', label: '通知记录', icon: 'fas fa-bell', path: '/notifications' },
            { id: 'reports', label: '生成报告', icon: 'fas fa-file-pdf', path: '/reports' },
            { id: 'settings', label: '系统设置', icon: 'fas fa-cog', path: '/settings' }
        ])

        const isActive = computed(() => (path) => {
            return route.path === path
        })

        return {
            navItems,
            isActive
        }
    }
}
</script>