<template>
    <div>
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                <i class="fas fa-tachometer-alt text-blue-500 mr-3"></i>
                监控仪表盘
            </h2>
            <div>
                <button
                    class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
                    <i class="fas fa-sync mr-2"></i> 刷新数据
                </button>
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard v-for="stat in stats" :key="stat.title" :title="stat.title" :value="stat.value" :icon="stat.icon"
                :trend="stat.trend" :color="stat.color" />
        </div>

        <!-- 实时反馈表格 -->
        <FeedbackTable :feedbacks="feedbacks" />

        <!-- 数据分析预览 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
            <div class="p-5 border-b border-gray-200 flex justify-between items-center">
                <h3 class="text-lg font-semibold text-gray-800">数据分析预览</h3>
                <button
                    class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
                    <i class="fas fa-chart-bar mr-2"></i> 查看完整分析
                </button>
            </div>
            <div class="p-5">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="chart-container bg-white p-4 border border-gray-200 rounded-lg">
                        <canvas ref="typeChart"></canvas>
                    </div>
                    <div class="chart-container bg-white p-4 border border-gray-200 rounded-lg">
                        <canvas ref="trendChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'
import StatCard from '../components/StatCard.vue'
import FeedbackTable from '../components/FeedbackTable.vue'
import { getRecentFeedbacks } from '../api/dashboard'

export default {
    name: 'Dashboard',
    components: {
        StatCard,
        FeedbackTable
    },
    setup() {
        const stats = ref([
            {
                title: '今日新增反馈',
                value: '24',
                icon: 'fas fa-comment-alt',
                trend: { type: 'up', value: '较昨日增加 20%' },
                color: 'blue'  // 蓝色背景 + 蓝色图标
            },
            {
                title: '待处理问题',
                value: '8',
                icon: 'fas fa-tasks',
                trend: { type: 'down', value: '较昨日减少 2' },
                color: 'orange'  // 橙色背景 + 橙色图标
            },
            {
                title: '关键词触发',
                value: '5',
                icon: 'fas fa-exclamation-triangle',
                trend: { type: 'alert', value: '需要立即关注' },
                color: 'red'  // 红色背景 + 红色图标
            },
            {
                title: '平均响应时间',
                value: '4.2h',
                icon: 'fas fa-clock',
                trend: { type: 'down', value: '较上周减少 0.8h' },
                color: 'green'  // 绿色背景 + 绿色图标
            }
        ])

        const feedbacks = ref([])
        const typeChart = ref(null)
        const trendChart = ref(null)

        const loadFeedbacks = async () => {
            try {
                const res = await getRecentFeedbacks(5)   // 调用统一接口
                feedbacks.value = res.data
            } catch (err) {
                console.error("加载反馈失败", err)
            }
        }

        onMounted(() => {
            // 初始化图表
            loadFeedbacks()

            new Chart(typeChart.value, {
                type: 'doughnut',
                data: {
                    labels: ['问题反馈', '人工服务', '解决方案', 'Win10专区'],
                    datasets: [{
                        data: [65, 15, 12, 8],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.7)',
                            'rgba(245, 158, 11, 0.7)',
                            'rgba(59, 130, 246, 0.7)',
                            'rgba(139, 92, 246, 0.7)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            })

            new Chart(trendChart.value, {
                type: 'line',
                data: {
                    labels: ['7月18日', '7月19日', '7月20日', '7月21日', '7月22日', '7月23日', '今日'],
                    datasets: [{
                        label: '问题数量',
                        data: [32, 28, 35, 40, 38, 42, 24],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.05)',
                        borderWidth: 3,
                        pointBackgroundColor: '#fff',
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            })
        })

        return {
            stats,
            feedbacks,
            typeChart,
            trendChart,
            loadFeedbacks
        }
    }
}
</script>