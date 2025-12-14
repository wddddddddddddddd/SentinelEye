<template>
    <div>
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                <i class="fas fa-tachometer-alt text-blue-500 mr-3"></i>
                监控仪表盘
            </h2>
            <div>
                <button @click="refreshData" :disabled="loading"
                    class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors disabled:opacity-50">
                    <i :class="['fas', loading ? 'fa-spinner fa-spin' : 'fa-sync', 'mr-2']"></i>
                    {{ loading ? '刷新中...' : '刷新数据' }}
                </button>
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard v-for="stat in stats" :key="stat.title" :title="stat.title" :value="stat.value" :icon="stat.icon"
                :trend="stat.trend" :color="stat.color" />
        </div>

        <!-- 实时反馈表格 -->
        <FeedbackTable :feedbacks="feedbacks" :loading="tableLoading" />
        <!-- 数据分析预览 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
            <div class="p-5 border-b border-gray-200 flex justify-between items-center">
                <h3 class="text-lg font-semibold text-gray-800">数据分析预览</h3>
                <div class="flex gap-2">
                    <button @click="refreshCharts"
                        class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
                        <i class="fas fa-redo mr-2"></i> 刷新数据
                    </button>
                    <button @click="viewFullAnalysis"
                        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
                        <i class="fas fa-chart-bar mr-2"></i> 查看完整分析
                    </button>
                </div>
            </div>
            <div class="p-5">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- 分类饼图 - 改为近7日 -->
                    <div class="chart-container">
                        <div class="flex items-center mb-4">
                            <i class="fas fa-chart-pie text-blue-500 text-lg mr-2"></i>
                            <h4 class="text-lg font-semibold text-gray-800">近7日反馈类型分布</h4>
                        </div>
                        <div ref="typeChart" style="width: 100%; height: 350px;"></div>
                        <div class="text-center text-sm text-gray-500 mt-2">
                            点击图例可以筛选/显示分类
                        </div>
                    </div>
                    <!-- 趋势图 - 改为近7日 -->
                    <div class="chart-container">
                        <div class="flex items-center mb-4">
                            <i class="fas fa-chart-line text-green-500 text-lg mr-2"></i>
                            <h4 class="text-lg font-semibold text-gray-800">近7日反馈趋势</h4>
                        </div>
                        <div ref="trendChart" style="width: 100%; height: 350px;"></div>
                        <div class="text-center text-sm text-gray-500 mt-2">
                            最近7天反馈问题数量趋势
                        </div>
                    </div>
                </div>

                <!-- 关键词触发统计 -->
                <div class="mt-8 pt-6 border-t border-gray-200">
                    <div class="flex items-center mb-4">
                        <i class="fas fa-key text-purple-500 text-lg mr-2"></i>
                        <h4 class="text-lg font-semibold text-gray-700">AI分析问题结果</h4>
                    </div>
                    <div v-if="keywordStats && keywordStats.length > 0" class="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <div v-for="item in keywordStats" :key="item.keyword"
                            class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center hover:bg-gray-100 transition-colors">
                            <div class="text-2xl font-bold text-gray-800 mb-1">{{ item.count }}</div>
                            <div class="text-sm text-gray-600 truncate">{{ item.keyword }}</div>
                            <div class="text-xs mt-1">
                                <span :class="{
                                    'text-green-500': item.trend === 'up',
                                    'text-red-500': item.trend === 'down',
                                    'text-gray-500': item.trend === 'stable'
                                }">
                                    {{ item.trend === 'up' ? '↑ 上升' : item.trend === 'down' ? '↓ 下降' : '→ 稳定' }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div v-else class="text-center py-8 text-gray-500">
                        暂无关键词触发数据
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import StatCard from '../components/StatCard.vue'
import FeedbackTable from '../components/FeedbackTable.vue'
import { getRecentFeedbacks, getDashboardStats, getChartData } from '../api/dashboard'
// 完整引入
import * as echarts from 'echarts'

export default {
    name: 'Dashboard',
    components: {
        StatCard,
        FeedbackTable
    },
    setup() {
        const stats = ref([])
        const feedbacks = ref([])
        const keywordStats = ref([])  // 关键词统计数据
        const typeChart = ref(null)
        const trendChart = ref(null)
        const loading = ref(false)
        const tableLoading = ref(false)
        const typeChartInstance = ref(null)  // 使用 ref 管理图表实例
        const trendChartInstance = ref(null) // 使用 ref 管理图表实例

        // 加载统计数据
        const loadStats = async () => {
            try {
                loading.value = true
                const res = await getDashboardStats()
                const data = res.data

                console.log("仪表盘数据:", data)

                // 1. 今日新增反馈 - 显示增长率
                const feedbackGrowthText = data.feedback_growth_rate !== 0
                    ? `${data.feedback_growth_rate > 0 ? '较昨日增加' : '较昨日减少'} ${Math.abs(data.feedback_growth_rate)}%`
                    : '与昨日持平'

                // 2. 待处理问题 - 显示差额
                const pendingDiffText = data.pending_difference !== 0
                    ? `${data.pending_difference > 0 ? '较昨日增加' : '较昨日减少'} ${Math.abs(data.pending_difference)}个`
                    : '与昨日持平'

                // 3. 关键词触发 - 显示最近3天情况
                const keywordTriggers = data.recent_keyword_triggers || []
                const totalKeywords = keywordTriggers.reduce((sum, item) => sum + item.count, 0)
                const topKeywords = keywordTriggers.slice(0, 3).map(k => k.keyword).join('、')
                const keywordText = keywordTriggers.length > 0
                    ? `近3天触发${totalKeywords}次，主要关键词：${topKeywords}`
                    : '近3天无关键词触发'

                // 4. 紧急反馈 - 今日紧急反馈
                const urgentText = data.today_urgent > 0
                    ? `今日新增${data.today_urgent}个紧急反馈`
                    : '今日无紧急反馈'

                // 动态设置统计数据
                stats.value = [
                    {
                        title: '今日新增反馈',
                        value: data.today_feedbacks.toString(),
                        icon: 'fas fa-comment-alt',
                        trend: {
                            type: data.feedback_growth_rate > 0 ? 'up' : data.feedback_growth_rate < 0 ? 'down' : 'stable',
                            value: feedbackGrowthText
                        },
                        color: 'blue'
                    },
                    {
                        title: '待处理问题',
                        value: data.today_pending.toString(), // 今日待处理数
                        icon: 'fas fa-tasks',
                        trend: {
                            type: data.pending_difference > 0 ? 'alert' : data.pending_difference < 0 ? 'down' : 'stable',
                            value: pendingDiffText
                        },
                        color: 'orange'
                    },
                    {
                        title: '关键词触发',
                        value: totalKeywords.toString(),
                        icon: 'fas fa-exclamation-triangle',
                        trend: {
                            type: totalKeywords > 0 ? 'alert' : 'normal',
                            value: keywordText
                        },
                        color: 'red'
                    },
                    {
                        title: 'AI Check',
                        value: data.today_urgent.toString(), // 今日紧急反馈数
                        icon: 'fas fa-fire',
                        trend: {
                            type: data.today_urgent > 0 ? 'alert' : 'normal',
                            value: urgentText
                        },
                        color: 'purple'
                    }
                ]

                // 更新关键词统计数据
                keywordStats.value = keywordTriggers

            } catch (err) {
                console.error("加载统计数据失败", err)
                // 出错时使用默认数据
                stats.value = getDefaultStats()
                keywordStats.value = []
            } finally {
                loading.value = false
            }
        }

        // 默认统计数据
        const getDefaultStats = () => {
            return [
                {
                    title: '今日新增反馈',
                    value: '0',
                    icon: 'fas fa-comment-alt',
                    trend: { type: 'normal', value: '数据加载中' },
                    color: 'blue'
                },
                {
                    title: '待处理问题',
                    value: '0',
                    icon: 'fas fa-tasks',
                    trend: { type: 'normal', value: '数据加载中' },
                    color: 'orange'
                },
                {
                    title: '关键词触发',
                    value: '0',
                    icon: 'fas fa-exclamation-triangle',
                    trend: { type: 'normal', value: '数据加载中' },
                    color: 'red'
                },
                {
                    title: 'AI Check',
                    value: '0',
                    icon: 'fas fa-fire',
                    trend: { type: 'normal', value: '数据加载中' },
                    color: 'purple'
                }
            ]
        }

        // 加载反馈数据
        const loadFeedbacks = async () => {
            try {
                tableLoading.value = true
                const res = await getRecentFeedbacks(5)
                feedbacks.value = res.data
            } catch (err) {
                console.error("加载反馈失败", err)
            } finally {
                tableLoading.value = false
            }
        }

        // 初始化图表
        // 初始化图表
        const initCharts = async () => {
            try {
                // 获取近7日图表数据，近3日关键词数据
                const chartRes = await getChartData(7, 3)  // 传入两个参数
                const chartData = chartRes.data

                console.log('近7日图表数据:', chartData)
                console.log('关键词触发数据:', chartData.keyword_triggers)

                // 1. 初始化分类饼图（近7日）
                initCategoryChart(chartData.category_data || [], chartData.total_feedbacks)

                // 2. 初始化趋势图（近7日，只显示反馈总数）
                initTrendChart(chartData.trend_data || {
                    dates: [],
                    feedbacks: []
                })

                // 3. 更新关键词触发数据
                keywordStats.value = chartData.keyword_triggers || []
                console.log('更新后的keywordStats:', keywordStats.value)

            } catch (error) {
                console.error("加载图表数据失败:", error)
                // 使用默认数据
                initDefaultCharts()
                keywordStats.value = []
            }
        }

        // 初始化分类饼图（近7日）
        const initCategoryChart = (categoryData, totalCount) => {
            const chartDom = typeChart.value
            if (!chartDom) return

            // 销毁之前的图表实例
            if (typeChartInstance.value) {
                typeChartInstance.value.dispose()
                typeChartInstance.value = null
            }

            const myChart = echarts.init(chartDom)

            // 获取分类颜色函数
            const getCategoryColor = (category) => {
                const colorMap = {
                    '问题反馈': '#10b981',      // 绿色
                    '人工服务': '#f59e0b',      // 橙色
                    '解决方案': '#3b82f6',      // 蓝色
                    'win10专区': '#8b5cf6',     // 紫色
                    '安全资讯': '#ef4444',      // 红色
                    '系统急救箱': '#06b6d4',    // 青色
                    '软件管家': '#ec4899',      // 粉色
                    '网购安全': '#84cc16',      // 黄绿色
                    '未分类': '#94a3b8',         // 灰色
                }
                return colorMap[category] || '#94a3b8'
            }

            // ECharts 配置 - 移除内置标题
            const option = {
                tooltip: {
                    trigger: 'item',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    textStyle: {
                        color: '#333'
                    },
                    formatter: '{b}: {c} ({d}%)'
                },
                legend: {
                    type: 'scroll',
                    orient: 'vertical',
                    right: 10,
                    top: 'middle',
                    textStyle: {
                        fontSize: 12,
                        color: '#666'
                    },
                    itemHeight: 12,
                    itemWidth: 12,
                    itemGap: 10
                },
                series: [
                    {
                        name: '反馈类型',
                        type: 'pie',
                        radius: ['45%', '75%'],
                        center: ['40%', '50%'],
                        avoidLabelOverlap: true,
                        itemStyle: {
                            borderRadius: 8,
                            borderColor: '#fff',
                            borderWidth: 2,
                            shadowColor: 'rgba(0, 0, 0, 0.1)',
                            shadowBlur: 5
                        },
                        label: {
                            show: false,
                            position: 'center',
                            formatter: '{b}\n{c}',
                            fontSize: 14,
                            fontWeight: 'bold'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 16,
                                fontWeight: 'bold'
                            },
                            itemStyle: {
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowColor: 'rgba(0, 0, 0, 0.3)'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: categoryData.map(item => ({
                            ...item,
                            itemStyle: {
                                color: getCategoryColor(item.name)
                            }
                        }))
                    }
                ],
            }

            myChart.setOption(option)

            // 监听窗口大小变化
            const resizeHandler = () => myChart.resize()
            window.addEventListener('resize', resizeHandler)

            // 保存图表实例
            typeChartInstance.value = myChart

            // 保存事件监听器以便清理
            typeChartInstance.value._resizeHandler = resizeHandler
        }

        // 初始化趋势图（近7日反馈问题数量趋势）
        const initTrendChart = (trendData) => {
            const chartDom = trendChart.value
            if (!chartDom) return

            // 销毁之前的图表实例
            if (trendChartInstance.value) {
                trendChartInstance.value.dispose()
                trendChartInstance.value = null
            }

            const myChart = echarts.init(chartDom)

            const option = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    axisPointer: {
                        type: 'cross',
                        label: {
                            backgroundColor: '#6a7985'
                        }
                    },
                    textStyle: {
                        color: '#333'
                    }
                },
                legend: {
                    data: ['反馈数量'],
                    top: 10,
                    textStyle: {
                        fontSize: 12,
                        color: '#666'
                    },
                    itemHeight: 10,
                    itemWidth: 10
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    top: '15%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: trendData.dates || [],
                    axisLine: {
                        lineStyle: {
                            color: '#ddd'
                        }
                    },
                    axisLabel: {
                        color: '#666',
                        rotate: 45 // 日期旋转45度，避免重叠
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    axisLine: {
                        lineStyle: {
                            color: '#ddd'
                        }
                    },
                    axisLabel: {
                        color: '#666'
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#f0f0f0',
                            type: 'dashed'
                        }
                    }
                },
                series: [
                    {
                        name: '反馈数量',
                        type: 'line',
                        smooth: true,
                        lineStyle: {
                            width: 4,
                            color: '#3b82f6'
                        },
                        itemStyle: {
                            color: '#3b82f6',
                            borderWidth: 2,
                            borderColor: '#fff'
                        },
                        symbol: 'circle',
                        symbolSize: 8,
                        areaStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                {
                                    offset: 0,
                                    color: 'rgba(59, 130, 246, 0.4)'
                                },
                                {
                                    offset: 1,
                                    color: 'rgba(59, 130, 246, 0.05)'
                                }
                            ])
                        },
                        data: trendData.feedbacks || []
                    }
                ],
                dataZoom: [
                    {
                        type: 'inside',
                        start: 0,
                        end: 100
                    }
                ]
            }

            myChart.setOption(option)

            // 监听窗口大小变化
            const resizeHandler = () => myChart.resize()
            window.addEventListener('resize', resizeHandler)

            // 保存图表实例
            trendChartInstance.value = myChart

            // 保存事件监听器以便清理
            trendChartInstance.value._resizeHandler = resizeHandler
        }

        // 默认图表（API失败时使用）
        const initDefaultCharts = () => {
            // 分类图 - 近7日模拟数据
            const defaultCategoryData = [
                { name: '问题反馈', value: 42 },
                { name: '人工服务', value: 18 },
                { name: '解决方案', value: 15 },
                { name: 'win10专区', value: 9 },
                { name: '安全资讯', value: 6 }
            ]
            initCategoryChart(defaultCategoryData, 90)

            // 趋势图 - 近7日模拟数据
            const defaultTrendData = {
                dates: ['12-01', '12-02', '12-03', '12-04', '12-05', '12-06', '12-07'],
                feedbacks: [12, 15, 18, 14, 16, 20, 13]
            }
            initTrendChart(defaultTrendData)
        }

        // 刷新数据
        const refreshData = async () => {
            try {
                loading.value = true
                await Promise.all([
                    loadStats(),
                    loadFeedbacks()
                ])
                await initCharts()
            } catch (error) {
                console.error("刷新数据失败:", error)
            } finally {
                loading.value = false
            }
        }

        // 刷新图表
        const refreshCharts = async () => {
            await initCharts()
        }

        // 查看完整分析
        const viewFullAnalysis = () => {
            alert('完整分析功能开发中...')
            // 这里可以跳转到详细分析页面
        }

        // 组件挂载时初始化
        onMounted(async () => {
            // 初始化时加载所有数据
            await refreshData()
        })

        // 组件卸载时清理
        onUnmounted(() => {
            // 销毁图表实例并移除事件监听
            if (typeChartInstance.value) {
                if (typeChartInstance.value._resizeHandler) {
                    window.removeEventListener('resize', typeChartInstance.value._resizeHandler)
                }
                typeChartInstance.value.dispose()
            }
            if (trendChartInstance.value) {
                if (trendChartInstance.value._resizeHandler) {
                    window.removeEventListener('resize', trendChartInstance.value._resizeHandler)
                }
                trendChartInstance.value.dispose()
            }
        })

        return {
            stats,
            feedbacks,
            keywordStats,
            typeChart,
            trendChart,
            loading,
            tableLoading,
            loadFeedbacks,
            refreshData,
            refreshCharts,
            viewFullAnalysis
        }
    }
}
</script>

<style scoped>
.chart-container {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.chart-container:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}

/* 图表标题样式优化 */
.chart-container h4 {
    position: relative;
    padding-bottom: 0.5rem;
}

.chart-container h4::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 40px;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #10b981);
    border-radius: 2px;
}
</style>