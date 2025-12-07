<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-chart-bar text-blue-500 mr-3"></i>
        数据分析
      </h2>
      <div class="flex gap-2">
        <button
          class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center transition-colors">
          <i class="fas fa-calendar mr-2"></i> 选择日期范围
        </button>
        <button
          class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
          <i class="fas fa-file-pdf mr-2"></i> 生成周报
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center mr-3">
            <i class="fas fa-comments text-blue-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">总反馈数</p>
            <p class="text-2xl font-bold text-gray-800">265</p>
          </div>
        </div>
        <div class="text-sm text-green-500">
          <i class="fas fa-arrow-up mr-1"></i>较上周增长12%
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center mr-3">
            <i class="fas fa-check-circle text-green-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">已处理</p>
            <p class="text-2xl font-bold text-gray-800">198</p>
          </div>
        </div>
        <div class="text-sm text-green-500">
          <i class="fas fa-arrow-up mr-1"></i>处理率74.7%
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center mr-3">
            <i class="fas fa-exclamation-triangle text-red-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">待处理</p>
            <p class="text-2xl font-bold text-gray-800">42</p>
          </div>
        </div>
        <div class="text-sm text-red-500">
          <i class="fas fa-arrow-down mr-1"></i>较上周增加5个
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div class="flex items-center mb-3">
          <div class="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center mr-3">
            <i class="fas fa-fire text-purple-500 text-lg"></i>
          </div>
          <div>
            <p class="text-sm text-gray-600">紧急反馈</p>
            <p class="text-2xl font-bold text-gray-800">25</p>
          </div>
        </div>
        <div class="text-sm text-purple-500">
          <i class="fas fa-arrow-up mr-1"></i>需重点关注
        </div>
      </div>
    </div>

    <!-- 主要分析图表 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="p-5 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <i class="fas fa-chart-pie text-blue-500 text-lg mr-2"></i>
            <h3 class="text-lg font-semibold text-gray-800">详细分析报告</h3>
          </div>
          <span class="text-sm text-gray-500">数据更新至：2024年12月7日</span>
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
              <h4 class="text-lg font-semibold text-gray-800">近7天反馈趋势</h4>
            </div>
            <div ref="trendChart" class="chart-container" style="width: 100%; height: 350px;"></div>
            <div class="text-center text-sm text-gray-500 mt-3">
              每日反馈数量变化趋势
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 横向分析图 -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
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
    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
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
              近7天高频关键词触发次数统计
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
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'Analytics',
  setup() {
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

    const initCharts = () => {
      // 初始化反馈类型分布图
      initTypeChart()

      // 初始化趋势图
      initTrendChart()

      // 初始化分类分析图
      initModuleChart()

      // 初始化关键词图表
      initKeywordCharts()
    }

    // 反馈类型分布图
    const initTypeChart = () => {
      if (!typeChart.value) return

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
            data: [
              { value: 142, name: '问题反馈', itemStyle: { color: '#10b981' } },
              { value: 45, name: '人工服务', itemStyle: { color: '#f59e0b' } },
              { value: 38, name: '解决方案', itemStyle: { color: '#3b82f6' } },
              { value: 22, name: 'win10专区', itemStyle: { color: '#8b5cf6' } },
              { value: 18, name: '安全资讯', itemStyle: { color: '#ef4444' } }
            ]
          }
        ],
      }

      myChart.setOption(option)
      typeChartInstance.value = myChart

      // 监听窗口变化
      const resizeHandler = () => myChart.resize()
      window.addEventListener('resize', resizeHandler)
      myChart._resizeHandler = resizeHandler
    }

    // 近7天反馈趋势图
    const initTrendChart = () => {
      if (!trendChart.value) return

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
          data: ['问题反馈', '人工服务'],
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
          data: ['12-01', '12-02', '12-03', '12-04', '12-05', '12-06', '12-07'],
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
            name: '问题反馈',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 4,
              color: '#10b981'
            },
            itemStyle: {
              color: '#10b981'
            },
            symbol: 'circle',
            symbolSize: 8,
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.05)' }
              ])
            },
            data: [32, 28, 35, 40, 38, 42, 24]
          },
          {
            name: '人工服务',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 4,
              color: '#f59e0b'
            },
            itemStyle: {
              color: '#f59e0b'
            },
            symbol: 'circle',
            symbolSize: 8,
            data: [12, 10, 14, 15, 13, 16, 8]
          }
        ]
      }

      myChart.setOption(option)
      trendChartInstance.value = myChart

      // 监听窗口变化
      const resizeHandler = () => myChart.resize()
      window.addEventListener('resize', resizeHandler)
      myChart._resizeHandler = resizeHandler
    }

    // 分类分析图（横向条形图）
    const initModuleChart = () => {
      if (!moduleChart.value) return

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
          data: ['问题反馈', '人工服务', '解决方案', 'win10专区', '安全资讯', '系统急救箱', '软件管家', '未分类'],
          axisLabel: {
            fontSize: 12
          }
        },
        series: [
          {
            name: '问题数量',
            type: 'bar',
            data: [
              { value: 142, itemStyle: { color: '#10b981' } },
              { value: 45, itemStyle: { color: '#f59e0b' } },
              { value: 38, itemStyle: { color: '#3b82f6' } },
              { value: 22, itemStyle: { color: '#8b5cf6' } },
              { value: 18, itemStyle: { color: '#ef4444' } },
              { value: 12, itemStyle: { color: '#06b6d4' } },
              { value: 8, itemStyle: { color: '#ec4899' } },
              { value: 15, itemStyle: { color: '#94a3b8' } }
            ],
            barWidth: 20,
            itemStyle: {
              borderRadius: [0, 10, 10, 0]
            }
          }
        ]
      }

      myChart.setOption(option)
      moduleChartInstance.value = myChart

      // 监听窗口变化
      const resizeHandler = () => myChart.resize()
      window.addEventListener('resize', resizeHandler)
      myChart._resizeHandler = resizeHandler
    }

    // 初始化关键词图表
    const initKeywordCharts = () => {
      // 关键词触发次数图
      initKeywordChart()

      // 关键词趋势图
      initKeywordTrendChart()
    }

    // 高频关键词触发次数
    const initKeywordChart = () => {
      if (!keywordChart.value) return

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
          data: ['崩溃', '错误', '无法启动', '闪退', '数据丢失', '系统错误', '卡顿', '网络问题'],
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
            data: [28, 24, 18, 15, 12, 10, 8, 7],
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#f59e0b' },
                { offset: 1, color: '#fbbf24' }
              ]),
              borderRadius: [5, 5, 0, 0]
            },
            barWidth: 30
          }
        ]
      }

      myChart.setOption(option)
      keywordChartInstance.value = myChart

      // 监听窗口变化
      const resizeHandler = () => myChart.resize()
      window.addEventListener('resize', resizeHandler)
      myChart._resizeHandler = resizeHandler
    }

    // 关键词触发趋势
    const initKeywordTrendChart = () => {
      if (!keywordTrendChart.value) return

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
          data: ['崩溃', '错误', '无法启动'],
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
          data: ['12-01', '12-02', '12-03', '12-04', '12-05', '12-06', '12-07'],
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
            name: '崩溃',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: '#ef4444'
            },
            itemStyle: {
              color: '#ef4444'
            },
            symbol: 'circle',
            symbolSize: 6,
            data: [5, 3, 6, 4, 5, 7, 5]
          },
          {
            name: '错误',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: '#f59e0b'
            },
            itemStyle: {
              color: '#f59e0b'
            },
            symbol: 'circle',
            symbolSize: 6,
            data: [4, 5, 3, 4, 6, 5, 4]
          },
          {
            name: '无法启动',
            type: 'line',
            smooth: true,
            lineStyle: {
              width: 3,
              color: '#8b5cf6'
            },
            itemStyle: {
              color: '#8b5cf6'
            },
            symbol: 'circle',
            symbolSize: 6,
            data: [3, 2, 4, 3, 2, 5, 3]
          }
        ]
      }

      myChart.setOption(option)
      keywordTrendChartInstance.value = myChart

      // 监听窗口变化
      const resizeHandler = () => myChart.resize()
      window.addEventListener('resize', resizeHandler)
      myChart._resizeHandler = resizeHandler
    }

    onMounted(() => {
      initCharts()
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
      keywordTrendChart
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