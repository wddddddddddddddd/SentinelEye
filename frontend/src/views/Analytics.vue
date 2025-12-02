<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-chart-bar text-blue-500 mr-3"></i>
        数据分析
      </h2>
      <div>
        <button
          class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center transition-colors">
          <i class="fas fa-file-pdf mr-2"></i> 生成周报
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
      <div class="p-5">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-4">问题类型分布</h3>
            <div class="chart-container">
              <canvas ref="typeChart"></canvas>
            </div>
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-4">问题趋势 (近7天)</h3>
            <div class="chart-container">
              <canvas ref="trendChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
      <div class="p-5">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">问题模块分析</h3>
        <div class="chart-container">
          <canvas ref="moduleChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Chart from 'chart.js/auto'

export default {
  name: 'Analytics',
  setup() {
    const typeChart = ref(null)
    const trendChart = ref(null)
    const moduleChart = ref(null)

    onMounted(() => {
      // 问题类型分布图表
      new Chart(typeChart.value, {
        type: 'bar',
        data: {
          labels: ['问题反馈', '人工服务', '解决方案', 'Win10专区', '其他'],
          datasets: [{
            label: '问题数量',
            data: [142, 45, 38, 22, 18],
            backgroundColor: '#3b82f6',
            borderRadius: 5,
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

      // 问题趋势图表
      new Chart(trendChart.value, {
        type: 'line',
        data: {
          labels: ['7月17日', '7月18日', '7月19日', '7月20日', '7月21日', '7月22日', '7月23日'],
          datasets: [{
            label: '问题反馈',
            data: [32, 28, 35, 40, 38, 42, 24],
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            borderWidth: 3,
            tension: 0.3
          }, {
            label: '人工服务',
            data: [12, 10, 14, 15, 13, 16, 8],
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderWidth: 3,
            tension: 0.3
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

      // 问题模块分析图表
      new Chart(moduleChart.value, {
        type: 'bar',
        data: {
          labels: ['安全防护', '系统优化', '软件管理', '网络防护', '隐私保护', '其他'],
          datasets: [{
            label: '问题数量',
            data: [56, 42, 38, 32, 28, 22],
            backgroundColor: [
              'rgba(59, 130, 246, 0.7)',
              'rgba(16, 185, 129, 0.7)',
              'rgba(245, 158, 11, 0.7)',
              'rgba(139, 92, 246, 0.7)',
              'rgba(236, 72, 153, 0.7)',
              'rgba(107, 114, 128, 0.7)'
            ],
            borderRadius: 5,
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          scales: {
            x: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              }
            },
            y: {
              grid: {
                display: false
              }
            }
          }
        }
      })
    })

    return {
      typeChart,
      trendChart,
      moduleChart
    }
  }
}
</script>