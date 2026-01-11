<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-chart-bar text-blue-500 mr-3"></i>
        周度数据分析
      </h2>
      <div class="flex gap-2 items-center">
        <!-- 周选择器 -->
        <div class="flex items-center bg-gray-100 rounded-lg p-1">
          <button @click="selectPreviousWeek" class="px-3 py-1 hover:bg-gray-200 rounded-lg transition-colors"
            :disabled="loading">
            <i class="fas fa-chevron-left"></i>
          </button>

          <div class="px-4 py-1 text-gray-700 font-medium min-w-[180px] text-center">
            {{ weekDisplay }}
          </div>

          <button @click="selectNextWeek" class="px-3 py-1 hover:bg-gray-200 rounded-lg transition-colors"
            :disabled="loading || isCurrentWeek">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>

        <!-- 快速切换按钮 -->
        <div class="flex gap-2">
          <button @click="selectCurrentWeek" :disabled="loading || isCurrentWeek"
            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50">
            本周
          </button>
          <button disabled="True" @click="generateReport" :disabled="generatingReport || loading"
            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center text-sm disabled:opacity-50">
            <i class="fas fa-file-pdf mr-2"></i>
            {{ generatingReport ? '生成中...' : '生成周报' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p class="text-gray-600">加载数据中...</p>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div class="flex items-center">
        <i class="fas fa-exclamation-triangle text-red-500 mr-3"></i>
        <div>
          <p class="text-red-700 font-medium">加载失败</p>
          <p class="text-red-600 text-sm">{{ error }}</p>
        </div>
        <button @click="fetchData" class="ml-auto text-sm text-blue-500 hover:text-blue-700">
          重试
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 stat-card">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mr-3">
            <i class="fas fa-comments text-blue-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">总反馈数</p>
            <p class="text-2xl font-bold text-gray-800">{{ overview.total_feedback || 0 }}</p>
          </div>
        </div>
        <div class="text-sm" :class="growthClass(overview.feedback_growth)">
          <i class="fas" :class="growthIcon(overview.feedback_growth)"></i>
          较上周{{ growthText(overview.feedback_growth) }}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 stat-card">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center mr-3">
            <i class="fas fa-check-circle text-green-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">已处理</p>
            <p class="text-2xl font-bold text-gray-800">{{ overview.resolved_feedback || 0 }}</p>
          </div>
        </div>
        <div class="text-sm" :class="growthClass(overview.resolution_rate)">
          <i class="fas" :class="growthIcon(overview.resolution_rate)"></i>
          较上周{{ growthText(overview.resolution_rate, '个') }}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 stat-card">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center mr-3">
            <i class="fas fa-exclamation-triangle text-red-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">待处理</p>
            <p class="text-2xl font-bold text-gray-800">{{ overview.pending_feedback || 0 }}</p>
          </div>
        </div>
        <div class="text-sm" :class="growthClass(overview.pending_change)">
          <i class="fas" :class="growthIcon(overview.pending_change)"></i>
          较上周{{ growthText(overview.pending_change, '个') }}
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 stat-card">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center mr-3">
            <i class="fas fa-fire text-purple-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">AI分析用户帖子数量</p>
            <p class="text-2xl font-bold text-gray-800">{{ overview.this_week_ai_check || 0 }}</p>
          </div>
        </div>
        <div class="text-sm text-purple-500">
          <i class="fas fa-exclamation mr-1"></i>占总反馈{{ overview.ai_check_week_percentage || 0 }}%
        </div>
      </div>
    </div>

    <!-- 主要分析图表 -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="p-5 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <i class="fas fa-chart-pie text-blue-500 text-lg mr-2"></i>
            <h3 class="text-lg font-semibold text-gray-800">详细分析报告</h3>
          </div>
          <span class="text-sm text-gray-500">周度数据：{{ weekDisplay }}</span>
        </div>
      </div>

      <div class="p-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- 问题类型分布 -->
          <div class="chart-section">
            <div class="flex items-center mb-4">
              <i class="fas fa-th-large text-blue-500 text-lg mr-2"></i>
              <h4 class="text-lg font-semibold text-gray-800">反馈类型分布</h4>
            </div>
            <div ref="typeChart" class="chart-container" style="width: 100%; height: 350px;"></div>
            <div class="text-center text-sm text-gray-500 mt-3">
              本周反馈类型统计分布
            </div>
          </div>

          <!-- 问题趋势 -->
          <div class="chart-section">
            <div class="flex items-center mb-4">
              <i class="fas fa-chart-line text-green-500 text-lg mr-2"></i>
              <h4 class="text-lg font-semibold text-gray-800">反馈趋势</h4>
            </div>
            <div ref="trendChart" class="chart-container" style="width: 100%; height: 350px;"></div>
            <div class="text-center text-sm text-gray-500 mt-3">
              本周每日反馈数量变化趋势(Top3 类型)
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 横向分析图 -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="p-5 border-b border-gray-200">
        <div class="flex items-center">
          <i class="fas fa-chart-bar text-purple-500 text-lg mr-2"></i>
          <h3 class="text-lg font-semibold text-gray-800">分类详细分析</h3>
        </div>
      </div>

      <div class="p-5">
        <div class="chart-section">
          <div class="flex items-center mb-4">
            <i class="fas fa-tags text-purple-500 text-lg mr-2"></i>
            <h4 class="text-lg font-semibold text-gray-800">主要分类问题数量排行</h4>
          </div>
          <div ref="moduleChart" class="chart-container" style="width: 100%; height: 400px;"></div>
          <div class="text-center text-sm text-gray-500 mt-3">
            本周问题数量分类排行
          </div>
        </div>
      </div>
    </div>

    <!-- 关键词分析 -->
    <div v-if="!loading && !error" class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="p-5 border-b border-gray-200">
        <div class="flex items-center">
          <i class="fas fa-key text-orange-500 text-lg mr-2"></i>
          <h3 class="text-lg font-semibold text-gray-800">关键词触发分析</h3>
        </div>
      </div>

      <div class="p-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- 关键词触发次数 -->
          <div class="chart-section">
            <div class="flex items-center mb-4">
              <i class="fas fa-exclamation-circle text-orange-500 text-lg mr-2"></i>
              <h4 class="text-lg font-semibold text-gray-800">高频关键词触发次数</h4>
            </div>
            <div ref="keywordChart" class="chart-container" style="width: 100%; height: 350px;"></div>
            <div class="text-center text-sm text-gray-500 mt-3">
              本周高频关键词触发次数统计
            </div>
          </div>

          <!-- 关键词趋势 -->
          <div class="chart-section">
            <div class="flex items-center mb-4">
              <i class="fas fa-chart-line text-red-500 text-lg mr-2"></i>
              <h4 class="text-lg font-semibold text-gray-800">关键词触发趋势</h4>
            </div>
            <div ref="keywordTrendChart" class="chart-container" style="width: 100%; height: 350px;"></div>
            <div class="text-center text-sm text-gray-500 mt-3">
              本周关键词触发趋势变化
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { analyticsApi, getWeekRange, formatDateChinese } from '../api/analytics'

export default {
  name: 'Analytics',
  setup() {
    // 图表 ref
    const typeChart = ref(null)
    const trendChart = ref(null)
    const moduleChart = ref(null)
    const keywordChart = ref(null)
    const keywordTrendChart = ref(null)

    const typeChartInstance = ref(null)
    const trendChartInstance = ref(null)
    const moduleChartInstance = ref(null)
    const keywordChartInstance = ref(null)
    const keywordTrendChartInstance = ref(null)

    // 状态
    const loading = ref(true)
    const error = ref(null)
    const generatingReport = ref(false)

    // 数据
    const overview = ref({})
    const typeDistribution = ref([])
    const trendData = ref({ dates: [], series: [] })
    const categoryData = ref([])
    const keywordData = ref({ top_keywords: [], keyword_trend: {} })

    // 当前选择的周（0表示本周，-1表示上周，1表示下周）
    const weekOffset = ref(0)

    // 计算当前周的日期范围
    const currentWeekRange = computed(() => {
      return getWeekRange(weekOffset.value)
    })

    // 显示文本：第X周
    const weekDisplay = computed(() => {
      if (weekOffset.value === 0) return '本周'
      if (weekOffset.value === -1) return '上周'
      if (weekOffset.value === 1) return '下周'
      return weekOffset.value < 0 ? `前${Math.abs(weekOffset.value)}周` : `后${weekOffset.value}周`
    })

    // 是否是当前周
    const isCurrentWeek = computed(() => weekOffset.value === 0)

    // 获取数据
    const fetchData = async () => {
      loading.value = true
      error.value = null

      try {
        const response = await analyticsApi.getAllAnalytics({
          start_date: currentWeekRange.value.start_date,
          end_date: currentWeekRange.value.end_date
        })

        overview.value = response.overview
        typeDistribution.value = response.type_distribution
        trendData.value = response.trend
        categoryData.value = response.category_analysis
        keywordData.value = response.keyword_analysis

        setTimeout(() => {
          initCharts()
        }, 100)

      } catch (err) {
        console.error('Error fetching analytics data:', err)
        error.value = '获取数据失败，请检查网络连接或联系管理员'
      } finally {
        loading.value = false
      }
    }

    // 周选择功能
    const selectCurrentWeek = () => {
      weekOffset.value = 0
      fetchData()
    }

    const selectPreviousWeek = () => {
      weekOffset.value -= 1
      fetchData()
    }

    const selectNextWeek = () => {
      weekOffset.value += 1
      fetchData()
    }

    // 增长相关计算函数
    const growthClass = (value) => {
      if (value > 0) return 'text-red-500'
      if (value < 0) return 'text-green-500'
      return 'text-gray-500'
    }

    const growthIcon = (value) => {
      if (value > 0) return 'fa-arrow-up'
      if (value < 0) return 'fa-arrow-down'
      return 'fa-minus'
    }

    const growthText = (value, unit = '%') => {
      if (value > 0) return `增长${Math.abs(value)}${unit}`
      if (value < 0) return `减少${Math.abs(value)}${unit}`
      return '持平'
    }

    // 生成报告
    const generateReport = async () => {
      generatingReport.value = true
      try {
        const response = await analyticsApi.generateWeeklyReport({
          start_date: currentWeekRange.value.start_date,
          end_date: currentWeekRange.value.end_date
        })

        const url = window.URL.createObjectURL(new Blob([response]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `周报_${currentWeekRange.value.start_date}_${currentWeekRange.value.end_date}.pdf`)
        document.body.appendChild(link)
        link.click()

        link.remove()
        window.URL.revokeObjectURL(url)

      } catch (err) {
        console.error('Error generating report:', err)
        alert('生成报告失败，请稍后重试')
      } finally {
        generatingReport.value = false
      }
    }

    // 图表初始化
    const initCharts = () => {
      initTypeChart()
      initTrendChart()
      initModuleChart()
      initKeywordCharts()
    }

    // 反馈类型分布图
    const initTypeChart = () => {
      if (!typeChart.value || !typeDistribution.value.length) return

      if (typeChartInstance.value) {
        typeChartInstance.value.dispose()
      }

      const myChart = echarts.init(typeChart.value)

      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'middle',
          textStyle: {
            fontSize: 12
          }
        },
        series: [
          {
            name: '反馈类型',
            type: 'pie',
            radius: ['45%', '70%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 8,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: typeDistribution.value.map(item => ({
              ...item,
              itemStyle: { color: item.color }
            }))
          }
        ],
      }

      myChart.setOption(option)
      typeChartInstance.value = myChart
      setupResizeHandler(myChart)
    }

    // 反馈趋势图
    const initTrendChart = () => {
      if (!trendChart.value || !trendData.value.dates.length) return

      if (trendChartInstance.value) {
        trendChartInstance.value.dispose()
      }

      const myChart = echarts.init(trendChart.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        legend: {
          data: trendData.value.series.map(s => s.name),
          top: 10,
          textStyle: {
            fontSize: 12
          }
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
          data: trendData.value.dates,
          axisLabel: {
            rotate: 45,
            formatter: function (value) {
              if (value.includes('-') && value.split('-').length === 3) {
                return value.split('-').slice(1).join('-')
              }
              return value
            }
          }
        },
        yAxis: {
          type: 'value',
          min: 0
        },
        series: trendData.value.series.map(series => ({
          name: series.name,
          type: 'line',
          smooth: true,
          lineStyle: {
            width: 4,
            color: series.color
          },
          itemStyle: {
            color: series.color
          },
          symbol: 'circle',
          symbolSize: 8,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: series.color + '30' },
              { offset: 1, color: series.color + '05' }
            ])
          },
          data: series.data
        }))
      }

      myChart.setOption(option)
      trendChartInstance.value = myChart
      setupResizeHandler(myChart)
    }

    // 分类分析图
    const initModuleChart = () => {
      if (!moduleChart.value || !categoryData.value.length) return

      if (moduleChartInstance.value) {
        moduleChartInstance.value.dispose()
      }

      const myChart = echarts.init(moduleChart.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '8%',
          bottom: '3%',
          top: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          boundaryGap: [0, 0.01]
        },
        yAxis: {
          type: 'category',
          data: categoryData.value.map(item => item.name),
          axisLabel: {
            fontSize: 12
          }
        },
        series: [
          {
            name: '问题数量',
            type: 'bar',
            data: categoryData.value.map(item => ({
              value: item.value,
              itemStyle: { color: item.color }
            })),
            barWidth: 20,
            itemStyle: {
              borderRadius: [0, 10, 10, 0]
            }
          }
        ]
      }

      myChart.setOption(option)
      moduleChartInstance.value = myChart
      setupResizeHandler(myChart)
    }

    // 关键词图表
    const initKeywordCharts = () => {
      initKeywordChart()
      initKeywordTrendChart()
    }

    // 高频关键词触发次数
    const initKeywordChart = () => {
      if (!keywordChart.value || !keywordData.value.top_keywords.length) return

      if (keywordChartInstance.value) {
        keywordChartInstance.value.dispose()
      }

      const myChart = echarts.init(keywordChart.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: keywordData.value.top_keywords.map(k => k.keyword),
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          min: 0
        },
        series: [
          {
            name: '触发次数',
            type: 'bar',
            data: keywordData.value.top_keywords.map(k => ({
              value: k.count,
              itemStyle: {
                color: k.color || new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: '#f59e0b' },
                  { offset: 1, color: '#fbbf24' }
                ])
              }
            })),
            barWidth: 30
          }
        ]
      }

      myChart.setOption(option)
      keywordChartInstance.value = myChart
      setupResizeHandler(myChart)
    }

    // 关键词触发趋势
    const initKeywordTrendChart = () => {
      if (!keywordTrendChart.value || !keywordData.value.keyword_trend.dates) return

      if (keywordTrendChartInstance.value) {
        keywordTrendChartInstance.value.dispose()
      }

      const myChart = echarts.init(keywordTrendChart.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        legend: {
          data: keywordData.value.keyword_trend.keywords,
          top: 10,
          textStyle: {
            fontSize: 12
          }
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
          data: keywordData.value.keyword_trend.dates,
          axisLabel: {
            rotate: 45,
            formatter: function (value) {
              if (value.includes('-') && value.split('-').length === 3) {
                return value.split('-').slice(1).join('-')
              }
              return value
            }
          }
        },
        yAxis: {
          type: 'value',
          min: 0
        },
        series: keywordData.value.keyword_trend.keywords.map((keyword, index) => {
          const colors = ['#ef4444', '#f59e0b', '#8b5cf6', '#10b981', '#3b82f6']
          return {
            name: keyword,
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: colors[index] || '#000'
            },
            itemStyle: {
              color: colors[index] || '#000'
            },
            symbol: 'circle',
            symbolSize: 6,
            data: keywordData.value.keyword_trend.data[keyword] || []
          }
        })
      }

      myChart.setOption(option)
      keywordTrendChartInstance.value = myChart
      setupResizeHandler(myChart)
    }

    // 设置窗口变化监听
    const setupResizeHandler = (chart) => {
      const resizeHandler = () => chart.resize()
      window.addEventListener('resize', resizeHandler)
      chart._resizeHandler = resizeHandler
    }

    // 生命周期
    onMounted(() => {
      fetchData()
    })

    onUnmounted(() => {
      const charts = [
        typeChartInstance,
        trendChartInstance,
        moduleChartInstance,
        keywordChartInstance,
        keywordTrendChartInstance
      ]

      charts.forEach(chart => {
        if (chart.value) {
          if (chart.value._resizeHandler) {
            window.removeEventListener('resize', chart.value._resizeHandler)
          }
          chart.value.dispose()
        }
      })
    })

    return {
      typeChart,
      trendChart,
      moduleChart,
      keywordChart,
      keywordTrendChart,
      loading,
      error,
      generatingReport,
      overview,
      weekDisplay,
      isCurrentWeek,
      selectCurrentWeek,
      selectPreviousWeek,
      selectNextWeek,
      generateReport,
      fetchData,
      growthClass,
      growthIcon,
      growthText
    }
  }
}
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 0.5rem;
}

.chart-section {
  background: white;
  border-radius: 0.75rem;
  padding: 1rem;
}

.stat-card {
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>