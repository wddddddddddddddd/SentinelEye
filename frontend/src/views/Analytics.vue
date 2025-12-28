<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-chart-bar text-blue-500 mr-3"></i>
        数据分析
      </h2>
      <div class="flex gap-2">
        <!-- 日期范围选择器 -->
        <div class="relative">
          <button @click="showDatePicker = !showDatePicker"
            class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
            <i class="fas fa-calendar mr-2"></i>
            {{ dateRangeDisplay }}
            <i class="fas fa-chevron-down ml-2 text-sm"></i>
          </button>

          <!-- 日期选择器下拉 -->
          <div v-if="showDatePicker" v-click-outside="closeDatePicker"
            class="absolute top-full mt-2 bg-white rounded-lg shadow-lg border border-gray-200 z-50 w-64">
            <div class="p-4">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">开始日期</label>
                <input type="date" v-model="dateRange.start_date"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">结束日期</label>
                <input type="date" v-model="dateRange.end_date"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div class="flex gap-2">
                <button @click="selectThisWeek"
                  class="flex-1 bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1 rounded text-sm">
                  本周
                </button>
                <button @click="selectLastWeek"
                  class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm">
                  上周
                </button>
                <button @click="selectLastMonth"
                  class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm">
                  上月
                </button>
              </div>
              <div class="flex justify-end mt-4">
                <button @click="applyDateRange"
                  class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm">
                  应用
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 生成周报按钮 -->
        <button @click="generateReport" :disabled="generatingReport"
          class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors disabled:opacity-50">
          <i class="fas fa-file-pdf mr-2"></i>
          {{ generatingReport ? '生成中...' : '生成周报' }}
        </button>
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
        <div class="text-sm"
          :class="overview.feedback_growth > 0 ? 'text-red-500' : overview.feedback_growth < 0 ? 'text-green-500' : 'text-gray-500'">
          <i class="fas"
            :class="overview.feedback_growth > 0 ? 'fa-arrow-up' : overview.feedback_growth < 0 ? 'fa-arrow-down' : 'fa-minus'"></i>
          较上周{{ overview.feedback_growth > 0 ? '增长' : overview.feedback_growth < 0 ? '减少' : '持平' }}{{
            overview.feedback_growth != 0 ? Math.abs(overview.feedback_growth) + '%' : '' }} </div>

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
          <div class="text-sm"
            :class="overview.resolution_rate > 0 ? 'text-red-500' : overview.resolution_rate < 0 ? 'text-green-500' : 'text-gray-500'">
            <i class="fas"
              :class="overview.resolution_rate > 0 ? 'fa-arrow-up' : overview.resolution_rate < 0 ? 'fa-arrow-down' : 'fa-minus'"></i>
            较上周{{ overview.resolution_rate > 0 ? '增加' : overview.resolution_rate < 0 ? '减少' : '持平' }}{{
              overview.resolution_rate != 0 ? Math.abs(overview.resolution_rate) + '个' : '' }} </div>
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
            <div class="text-sm"
              :class="overview.pending_change > 0 ? 'text-red-500' : overview.pending_change < 0 ? 'text-green-500' : 'text-gray-500'">
              <i class="fas"
                :class="overview.pending_change > 0 ? 'fa-arrow-up' : overview.pending_change < 0 ? 'fa-arrow-down' : 'fa-minus'"></i>
              较上周{{ overview.pending_change > 0 ? '增加' : overview.pending_change < 0 ? '减少' : '持平' }}{{
                overview.pending_change != 0 ? Math.abs(overview.pending_change) + '个' : '' }} </div>
            </div>

            <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5 stat-card">
              <div class="flex items-center mb-3">
                <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center mr-3">
                  <i class="fas fa-fire text-purple-500 text-lg"></i>
                </div>
                <div>
                  <p class="text-sm text-gray-600">紧急反馈</p>
                  <p class="text-2xl font-bold text-gray-800">{{ overview.urgent_feedback || 0 }}</p>
                </div>
              </div>
              <div class="text-sm text-purple-500">
                <i class="fas fa-exclamation mr-1"></i>占总反馈{{ overview.urgent_percentage || 0 }}%
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
                <span class="text-sm text-gray-500">数据更新至：{{ formatDateChinese(dateRange.end_date) }}</span>
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
                    按反馈类型统计分布情况
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
                    每日反馈数量变化趋势(Top3 类型)
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
                  按问题数量排序的主要分类排行
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
                    高频关键词触发次数统计
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
                    主要关键词触发趋势变化
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
import { analyticsApi, getCurrentWeekRange, formatDate, formatDateChinese } from '../api/analytics'

export default {
  name: 'Analytics',
  setup() {
    // 图表 ref（保持不变）
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
    const showDatePicker = ref(false)
    const generatingReport = ref(false)

    // 数据
    const overview = ref({})
    const typeDistribution = ref([])
    const trendData = ref({ dates: [], series: [] })
    const categoryData = ref([])
    const keywordData = ref({ top_keywords: [], keyword_trend: {} })

    // 日期范围 - 默认本周
    const defaultDateRange = getCurrentWeekRange()
    const dateRange = ref({
      start_date: defaultDateRange.start_date,
      end_date: defaultDateRange.end_date
    })

    // 计算属性：显示日期范围
    const dateRangeDisplay = computed(() => {
      const start = formatDateChinese(dateRange.value.start_date)
      const end = formatDateChinese(dateRange.value.end_date)
      return `${start} - ${end}`
    })

    // 获取数据 - 修改为调用真实 API
    const fetchData = async () => {
      loading.value = true
      error.value = null

      try {
        // 方式1：一次性获取所有数据
        const response = await analyticsApi.getAllAnalytics(dateRange.value)

        // 更新数据
        overview.value = response.overview
        typeDistribution.value = response.type_distribution
        trendData.value = response.trend
        categoryData.value = response.category_analysis
        keywordData.value = response.keyword_analysis

        // 重新渲染图表
        setTimeout(() => {
          initCharts()
        }, 100)

      } catch (err) {
        console.error('Error fetching analytics data:', err)

        // 如果 API 失败，显示错误信息，也可以选择使用备用模拟数据
        error.value = '获取数据失败，请检查网络连接或联系管理员'

        // 备用方案：如果后端未启动，可以暂时用本地模拟数据
        // const mockData = await getLocalMockData()
        // overview.value = mockData.overview
        // ... 其他数据赋值
      } finally {
        loading.value = false
      }
    }

    // 本地备用数据（可选，当后端不可用时使用）
    const getLocalMockData = async () => {
      const startDate = new Date(dateRange.value.start_date)
      const endDate = new Date(dateRange.value.end_date)
      const diffTime = Math.abs(endDate - startDate)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const dates = []
      for (let i = 0; i <= diffDays && i < 7; i++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + i)
        dates.push(formatDate(date))
      }

      return {
        overview: {
          total_feedback: 265,
          resolved_feedback: 198,
          pending_feedback: 42,
          urgent_feedback: 25,
          feedback_growth: 12,
          pending_change: 5,
          resolution_rate: 74.7,
          urgent_percentage: 9.4
        },
        type_distribution: [
          { name: '问题反馈', value: 142, color: '#10b981' },
          { name: '人工服务', value: 45, color: '#f59e0b' },
          { name: '解决方案', value: 38, color: '#3b82f6' },
          { name: 'win10专区', value: 22, color: '#8b5cf6' },
          { name: '安全资讯', value: 18, color: '#ef4444' }
        ],
        trend: {
          dates: dates,
          series: [
            {
              name: '问题反馈',
              data: [32, 28, 35, 40, 38, 42, 24],
              color: '#10b981'
            },
            {
              name: '人工服务',
              data: [12, 10, 14, 15, 13, 16, 8],
              color: '#f59e0b'
            }
          ]
        },
        category_analysis: [
          { name: '问题反馈', value: 142, color: '#10b981' },
          { name: '人工服务', value: 45, color: '#f59e0b' },
          { name: '解决方案', value: 38, color: '#3b82f6' },
          { name: 'win10专区', value: 22, color: '#8b5cf6' },
          { name: '安全资讯', value: 18, color: '#ef4444' },
          { name: '系统急救箱', value: 12, color: '#06b6d4' },
          { name: '软件管家', value: 8, color: '#ec4899' },
          { name: '未分类', value: 15, color: '#94a3b8' }
        ],
        keyword_analysis: {
          top_keywords: [
            { keyword: '崩溃', count: 28, color: '#ef4444' },
            { keyword: '错误', count: 24, color: '#f59e0b' },
            { keyword: '无法启动', count: 18, color: '#8b5cf6' },
            { keyword: '闪退', count: 15, color: '#10b981' },
            { keyword: '数据丢失', count: 12, color: '#3b82f6' },
            { keyword: '系统错误', count: 10, color: '#ec4899' }
          ],
          keyword_trend: {
            dates: dates,
            keywords: ['崩溃', '错误', '无法启动'],
            data: {
              '崩溃': [5, 3, 6, 4, 5, 7, 5],
              '错误': [4, 5, 3, 4, 6, 5, 4],
              '无法启动': [3, 2, 4, 3, 2, 5, 3]
            }
          }
        }
      }
    }

    // 日期选择器操作
    const selectThisWeek = () => {
      const weekRange = getCurrentWeekRange()
      dateRange.value = {
        start_date: weekRange.start_date,
        end_date: weekRange.end_date
      }
      fetchData() // 自动获取新数据
    }

    const selectLastWeek = () => {
      const now = new Date()
      const lastWeek = new Date(now)
      lastWeek.setDate(now.getDate() - 7)
      const weekRange = getCurrentWeekRange(lastWeek)

      dateRange.value = {
        start_date: weekRange.start_date,
        end_date: weekRange.end_date
      }
      fetchData() // 自动获取新数据
    }

    const selectLastMonth = () => {
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      const end = new Date(now.getFullYear(), now.getMonth(), 0)

      dateRange.value = {
        start_date: formatDate(start),
        end_date: formatDate(end)
      }
      fetchData() // 自动获取新数据
    }

    const applyDateRange = () => {
      showDatePicker.value = false
      fetchData()
    }

    const closeDatePicker = () => {
      showDatePicker.value = false
    }

    // 生成报告 - 修改为调用真实 API
    const generateReport = async () => {
      generatingReport.value = true
      try {
        // 调用后端 API 生成报告
        const response = await analyticsApi.generateWeeklyReport(dateRange.value)

        // 假设后端返回的是文件流
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `周报_${dateRange.value.start_date}_${dateRange.value.end_date}.pdf`)
        document.body.appendChild(link)
        link.click()

        // 清理
        link.remove()
        window.URL.revokeObjectURL(url)

        // 如果后端返回的是 JSON（包含下载链接）
        // window.open(response.download_url, '_blank')

      } catch (err) {
        console.error('Error generating report:', err)
        alert('生成报告失败，请稍后重试')
      } finally {
        generatingReport.value = false
      }
    }

    // 图表初始化（保持不变，但会根据实际数据渲染）
    const initCharts = () => {
      initTypeChart()
      initTrendChart()
      initModuleChart()
      initKeywordCharts()
    }

    // 反馈类型分布图 - 根据实际数据渲染
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

    // 反馈趋势图 - 根据实际数据渲染
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
              // 如果是完整日期，只显示月日
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

    // 分类分析图 - 根据实际数据渲染
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

    // 关键词图表 - 根据实际数据渲染
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
              // 如果是完整日期，只显示月日
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
      // 清理所有图表实例
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
      showDatePicker,
      generatingReport,
      overview,
      dateRange,
      dateRangeDisplay,
      formatDateChinese,
      selectThisWeek,
      selectLastWeek,
      selectLastMonth,
      applyDateRange,
      closeDatePicker,
      generateReport,
      fetchData
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