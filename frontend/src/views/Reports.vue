<template>
  <div class="min-h-screen bg-gray-50 p-6">
    <!-- 气泡通知 -->
    <div v-if="showNotification" class="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div :class="[
        'px-6 py-4 rounded-lg shadow-lg border-l-4 flex items-center',
        notificationType === 'success' ? 'bg-green-50 border-green-500 text-green-800' :
          notificationType === 'error' ? 'bg-red-50 border-red-500 text-red-800' :
            notificationType === 'warning' ? 'bg-yellow-50 border-yellow-500 text-yellow-800' :
              'bg-blue-50 border-blue-500 text-blue-800'
      ]">
        <div class="mr-3">
          <i :class="[
            'fas text-lg',
            notificationType === 'success' ? 'fa-check-circle text-green-500' :
              notificationType === 'error' ? 'fa-exclamation-circle text-red-500' :
                notificationType === 'warning' ? 'fa-exclamation-triangle text-yellow-500' :
                  'fa-info-circle text-blue-500'
          ]"></i>
        </div>
        <div>
          <p class="font-medium">{{ notificationTitle }}</p>
          <p class="text-sm opacity-90">{{ notificationMessage }}</p>
        </div>
        <button @click="showNotification = false" class="ml-4 text-gray-500 hover:text-gray-700">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <div class="max-w-7xl mx-auto">
      <!-- 标题 -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">报告管理</h1>
        <p class="text-gray-600 mt-2">生成和查看用户反馈分析报告</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 生成面板 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-xl shadow p-6">
            <h2 class="text-xl font-bold mb-4">生成新报告</h2>

            <!-- 快速选择 -->
            <div class="mb-6">
              <label class="block text-sm font-medium mb-2">快速选择</label>
              <div class="flex flex-wrap gap-2 mb-4">
                <button v-for="opt in quickOptions" :key="opt.value" @click="setQuickDate(opt.value)"
                  class="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg">
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <!-- 自定义日期 -->
            <div class="mb-6">
              <label class="block text-sm font-medium mb-2">自定义范围</label>
              <div class="space-y-3">
                <div>
                  <span class="text-sm text-gray-500 block mb-1">开始日期</span>
                  <input type="date" v-model="startDate" :max="endDate" class="w-full p-2 border rounded-lg" />
                </div>
                <div>
                  <span class="text-sm text-gray-500 block mb-1">结束日期</span>
                  <input type="date" v-model="endDate" :min="startDate" class="w-full p-2 border rounded-lg" />
                </div>
              </div>
            </div>

            <!-- 报告类型 -->
            <div class="mb-6">
              <label class="block text-sm font-medium mb-2">报告类型</label>
              <div class="space-y-2">
                <label class="flex items-center">
                  <input type="radio" v-model="reportType" value="weekly" class="h-4 w-4 text-blue-600" />
                  <span class="ml-2 text-gray-700">周报</span>
                </label>
                <label class="flex items-center">
                  <input type="radio" v-model="reportType" value="monthly" class="h-4 w-4 text-blue-600" />
                  <span class="ml-2 text-gray-700">月报</span>
                </label>
                <label class="flex items-center">
                  <input type="radio" v-model="reportType" value="custom" class="h-4 w-4 text-blue-600" />
                  <span class="ml-2 text-gray-700">自定义报告</span>
                </label>
              </div>
            </div>

            <!-- 生成按钮 -->
            <button @click="generateReport" :disabled="loading"
              class="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center">
              <span v-if="loading" class="flex items-center">
                <svg class="animate-spin h-5 w-5 mr-2 text-white" xmlns="http://www.w3.org/2000/svg" fill="none"
                  viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                  </path>
                </svg>
                生成中...
              </span>
              <span v-else>生成报告</span>
            </button>

            <!-- 生成进度 -->
            <div v-if="generationSteps.length > 0" class="mt-6">
              <h3 class="text-sm font-medium mb-3">生成进度</h3>
              <div class="space-y-2">
                <div v-for="(step, index) in generationSteps" :key="index" class="flex items-center">
                  <div :class="[
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs mr-3',
                    step.status === 'completed' ? 'bg-green-500 text-white' :
                      step.status === 'processing' ? 'bg-blue-500 text-white' :
                        'bg-gray-200 text-gray-500'
                  ]">
                    {{ getStepStatusIcon(step.status) }}
                  </div>
                  <div class="flex-1">
                    <div class="text-sm">{{ step.name }}</div>
                    <div v-if="step.details" class="text-xs text-gray-500">{{ step.details }}</div>
                    <div class="text-xs text-gray-400">
                      {{ step.timestamp ? step.timestamp : '' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="lg:col-span-2">
          <!-- 当前报告 -->
          <div v-if="currentReport" class="mb-6">
            <div class="bg-white rounded-xl shadow p-6">
              <div class="flex justify-between items-start mb-4">
                <div>
                  <h3 class="text-lg font-bold">最新报告</h3>
                  <p class="text-sm text-gray-600">
                    {{ formatDate(currentReport.start_date) }} - {{ formatDate(currentReport.end_date) }}
                    <span class="ml-2 text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      {{ currentReport.type === 'weekly' ? '周报' : currentReport.type === 'monthly' ? '月报' : '自定义' }}
                    </span>
                    <span v-if="currentReport.status" :class="[
                      'ml-2 text-xs px-2 py-1 rounded',
                      currentReport.status === 'completed' ? 'bg-green-100 text-green-800' :
                        currentReport.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                          'bg-red-100 text-red-800'
                    ]">
                      {{ currentReport.status === 'completed' ? '已完成' : currentReport.status === 'processing' ? '进行中' :
                        '失败' }}
                    </span>
                  </p>
                </div>
                <div class="text-sm text-gray-500">
                  生成时间: {{ formatDateTime(currentReport.created_at) }}
                </div>
              </div>

              <!-- 统计卡片 -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="p-4 bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-500">总反馈</p>
                  <p class="text-2xl font-bold">{{ currentReport.stats?.total || 0 }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-500">高风险</p>
                  <p class="text-2xl font-bold text-red-600">{{ currentReport.stats?.risk_level?.high || 0 }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-500">需跟进</p>
                  <p class="text-2xl font-bold text-amber-600">{{ currentReport.stats?.need_followup || 0 }}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-500">AI分析</p>
                  <p class="text-2xl font-bold text-green-600">
                    {{ Math.round((currentReport.stats?.ai_analyzed / (currentReport.stats?.total || 1)) * 100) }}%
                  </p>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex gap-3">
                <button @click="previewReport(currentReport)" :disabled="currentReport.status !== 'completed'" :class="[
                  'px-4 py-2 border rounded-lg',
                  currentReport.status === 'completed' ? 'hover:bg-gray-50' : 'opacity-50 cursor-not-allowed'
                ]">
                  预览
                </button>
                <button @click="downloadPDF(currentReport.id)" :disabled="!currentReport.has_pdf" :class="[
                  'px-4 py-2 bg-blue-600 text-white rounded-lg',
                  currentReport.has_pdf ? 'hover:bg-blue-700' : 'opacity-50 cursor-not-allowed'
                ]">
                  下载PDF
                </button>
              </div>
            </div>
          </div>

          <!-- 历史报告列表 -->
          <div class="bg-white rounded-xl shadow overflow-hidden">
            <div class="p-6 border-b">
              <h3 class="text-lg font-bold">历史报告</h3>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="p-4 text-left text-sm font-medium text-gray-700">时间范围</th>
                    <th class="p-4 text-left text-sm font-medium text-gray-700">类型</th>
                    <th class="p-4 text-left text-sm font-medium text-gray-700">统计数据</th>
                    <th class="p-4 text-left text-sm font-medium text-gray-700">生成时间</th>
                    <th class="p-4 text-left text-sm font-medium text-gray-700">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="report in reports" :key="report.id" class="border-t hover:bg-gray-50">
                    <!-- 时间范围 -->
                    <td class="p-4">
                      <div class="font-medium">{{ formatDate(report.start_date) }} 至 {{ formatDate(report.end_date) }}
                      </div>
                      <div class="text-sm text-gray-500">{{ getDateRangeDays(report.start_date, report.end_date) }}天
                      </div>
                    </td>

                    <!-- 类型 -->
                    <td class="p-4">
                      <span :class="[
                        'px-3 py-1 text-xs font-medium rounded-full',
                        report.type === 'weekly' ? 'bg-blue-100 text-blue-800' :
                          report.type === 'monthly' ? 'bg-purple-100 text-purple-800' :
                            'bg-gray-100 text-gray-800'
                      ]">
                        {{ report.type === 'weekly' ? '周报' : report.type === 'monthly' ? '月报' : '自定义' }}
                      </span>
                      <span v-if="report.status" :class="[
                        'ml-1 text-xs px-2 py-0.5 rounded',
                        report.status === 'completed' ? 'bg-green-100 text-green-800' :
                          report.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                            'bg-red-100 text-red-800'
                      ]">
                        {{ report.status === 'completed' ? '✓' : report.status === 'processing' ? '⏳' : '✗' }}
                      </span>
                    </td>

                    <!-- 统计数据 -->
                    <td class="p-4">
                      <div class="space-y-1">
                        <div class="flex items-center">
                          <span class="text-sm text-gray-500 w-16">总反馈:</span>
                          <span class="font-medium">{{ report.stats?.total || 0 }}</span>
                        </div>
                        <div class="flex items-center">
                          <span class="text-sm text-gray-500 w-16">高风险:</span>
                          <span class="font-medium text-red-600">{{ report.stats?.risk_level?.high || 0 }}</span>
                        </div>
                        <div class="flex items-center">
                          <span class="text-sm text-gray-500 w-16">需跟进:</span>
                          <span class="font-medium text-amber-600">{{ report.stats?.need_followup || 0 }}</span>
                        </div>
                      </div>
                    </td>

                    <!-- 生成时间 -->
                    <td class="p-4">
                      <div class="text-sm">{{ formatDate(report.created_at) }}</div>
                      <div class="text-xs text-gray-500">{{ report.created_at }}</div>
                    </td>

                    <!-- 操作 -->
                    <td class="p-4">
                      <div class="flex gap-2">
                        <button @click="previewReport(report)" :disabled="report.status !== 'completed'" :class="[
                          'px-3 py-1 text-sm text-blue-600 rounded',
                          report.status === 'completed' ? 'hover:bg-blue-50' : 'opacity-50 cursor-not-allowed'
                        ]" title="预览">
                          预览
                        </button>
                        <button @click="downloadPDF(report.id)" :disabled="!report.has_pdf" :class="[
                          'px-3 py-1 text-sm bg-blue-600 text-white rounded',
                          report.has_pdf ? 'hover:bg-blue-700' : 'opacity-50 cursor-not-allowed'
                        ]" title="下载">
                          下载
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div v-if="reports.length === 0" class="p-8 text-center text-gray-500">
              暂无历史报告
            </div>
          </div>
        </div>
      </div>

      <!-- 预览模态框 -->
      <div v-if="showPreview" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
          <div class="p-6 border-b flex justify-between items-center">
            <div>
              <h3 class="text-xl font-bold">报告预览</h3>
              <p class="text-sm text-gray-600 mt-1">
                {{ previewReportData?.start_date ? formatDate(previewReportData.start_date) : '' }} -
                {{ previewReportData?.end_date ? formatDate(previewReportData.end_date) : '' }}
              </p>
            </div>
            <button @click="closePreview" class="p-2 hover:bg-gray-100 rounded text-gray-500">
              关闭
            </button>
          </div>

          <div class="flex-1 overflow-auto p-6">
            <div v-if="previewContent" v-html="previewContent" class="prose max-w-none"></div>
            <div v-else class="text-center py-8 text-gray-500">
              加载中...
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { marked } from 'marked'

// API基础URL
const API_BASE = 'http://127.0.0.1:8888/api/reports'

// 气泡通知状态
const showNotification = ref(false)
const notificationType = ref('info') // success, error, warning, info
const notificationTitle = ref('')
const notificationMessage = ref('')

// 所有状态和函数都必须在顶层声明
const loading = ref(false)
const startDate = ref('')
const endDate = ref('')
const reportType = ref('weekly')
const currentReport = ref(null)
const reports = ref([])
const showPreview = ref(false)
const previewContent = ref('')
const previewReportData = ref(null)
const generationSteps = ref([])
const pollingInterval = ref(null)

// 配置
const quickOptions = [
  { label: '最近7天', value: '7days' },
  { label: '最近30天', value: '30days' },
  { label: '本月', value: 'month' },
  { label: '上月', value: 'lastMonth' }
]

// ============ 气泡通知函数 ============

// 显示气泡通知
const showToast = (type, message, title = '', duration = 3000) => {
  notificationType.value = type
  notificationMessage.value = message
  notificationTitle.value = title || getDefaultTitle(type)
  showNotification.value = true

  // 如果已经有通知，先关闭再重新显示
  clearTimeout(showNotification.timeout)

  showNotification.timeout = setTimeout(() => {
    showNotification.value = false
  }, duration)
}

// 获取默认标题
const getDefaultTitle = (type) => {
  switch (type) {
    case 'success':
      return '操作成功'
    case 'error':
      return '操作失败'
    case 'warning':
      return '提示'
    case 'info':
      return '信息'
    default:
      return '通知'
  }
}

// 显示成功通知
const showSuccess = (message, title = '操作成功') => {
  showToast('success', message, title)
}

// 显示错误通知
const showError = (message, title = '操作失败') => {
  showToast('error', message, title)
}

// 显示警告通知
const showWarning = (message, title = '提示') => {
  showToast('warning', message, title)
}

// 显示信息通知
const showInfo = (message, title = '信息') => {
  showToast('info', message, title)
}

// ============ 所有函数都必须在顶层声明 ============

// 获取当月第一天
const getFirstDayOfMonth = (date = new Date()) => {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}

// 获取当月最后一天
const getLastDayOfMonth = (date = new Date()) => {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0)
}

// 获取上月第一天
const getFirstDayOfLastMonth = (date = new Date()) => {
  return new Date(date.getFullYear(), date.getMonth() - 1, 1)
}

// 获取上月最后一天
const getLastDayOfLastMonth = (date = new Date()) => {
  return new Date(date.getFullYear(), date.getMonth(), 0)
}

// 设置快速日期（修复版）
const setQuickDate = (type) => {
  const now = new Date()
  let start = new Date()
  let end = new Date()

  switch (type) {
    case '7days':
      // 最近7天：从7天前到今天
      start.setDate(now.getDate() - 7)
      end = new Date(now) // 今天
      break
    case '30days':
      // 最近30天：从30天前到今天
      start.setDate(now.getDate() - 30)
      end = new Date(now) // 今天
      break
    case 'month':
      // 本月：从当月1号到今天（如果今天不是1号的话）
      start = getFirstDayOfMonth(now)
      end = new Date(now) // 今天

      // 如果今天是1号，则设置为当天
      if (now.getDate() === 1) {
        start = new Date(now)
      }
      break
    case 'lastMonth':
      // 上月：从上月1号到上月最后一天
      start = getFirstDayOfLastMonth(now)
      end = getLastDayOfLastMonth(now)
      break
  }

  // 格式化日期
  startDate.value = formatDateInput(start)
  endDate.value = formatDateInput(end)

  console.log('快速选择:', type, '开始:', startDate.value, '结束:', endDate.value)
}

// 生成报告
const generateReport = async () => {
  if (loading.value) return

  // 验证日期
  if (!startDate.value || !endDate.value) {
    showWarning('请选择日期范围')
    return
  }

  const start = new Date(startDate.value)
  const end = new Date(endDate.value)

  if (start > end) {
    showWarning('开始日期不能晚于结束日期')
    return
  }

  // 验证日期范围不超过一年（可选，根据业务需求调整）
  const oneYearAgo = new Date()
  oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1)
  if (start < oneYearAgo) {
    showWarning('开始日期不能超过一年前')
    return
  }

  loading.value = true
  generationSteps.value = []

  try {
    console.log('开始生成报告，参数:', {
      start_date: startDate.value,
      end_date: endDate.value,
      report_type: reportType.value
    })

    const response = await axios.post(`${API_BASE}/generate`, {
      start_date: startDate.value,
      end_date: endDate.value,
      report_type: reportType.value
    })

    console.log('生成报告响应:', response.data)

    if (response.data.success) {
      const reportId = response.data.data.report_id
      startPollingReportStatus(reportId)
      showInfo('报告生成任务已启动，请等待完成...')
    } else {
      showError('启动失败: ' + (response.data.error || '未知错误'))
      loading.value = false
    }
  } catch (error) {
    console.error('生成失败:', error)
    let errorMessage = '生成失败: '

    if (error.response) {
      errorMessage += error.response.data?.detail || error.response.statusText || '服务器错误'
      console.error('错误详情:', error.response.data)
    } else if (error.request) {
      errorMessage += '网络请求失败，请检查网络连接'
    } else {
      errorMessage += error.message
    }

    showError(errorMessage)
    loading.value = false
  }
}

// 轮询报告状态
const startPollingReportStatus = (reportId) => {
  // 清理现有的轮询
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }

  console.log(`开始轮询报告状态，报告ID: ${reportId}`)

  pollingInterval.value = setInterval(async () => {
    try {
      const statusResponse = await axios.get(`${API_BASE}/${reportId}/status`)
      console.log('轮询状态响应:', statusResponse.data)

      if (statusResponse.data.success) {
        const reportData = statusResponse.data.data

        // 更新步骤进度
        generationSteps.value = reportData.steps || []

        if (reportData.status === 'completed') {
          console.log('报告生成完成')
          clearInterval(pollingInterval.value)
          pollingInterval.value = null
          loading.value = false

          await loadReportDetails(reportId)
          await loadReportsList()
          showSuccess('报告生成完成！')
        } else if (reportData.status === 'failed') {
          console.log('报告生成失败:', reportData.error_message)
          clearInterval(pollingInterval.value)
          pollingInterval.value = null
          loading.value = false
          showError(`报告生成失败: ${reportData.error_message || '未知错误'}`)
        }
      }
    } catch (error) {
      console.error('轮询状态失败:', error)
      // 不停止轮询，可能是临时网络问题
    }
  }, 3000) // 每3秒轮询一次
}

// 加载报告详情
const loadReportDetails = async (reportId) => {
  try {
    console.log(`加载报告详情，报告ID: ${reportId}`)

    const contentResponse = await axios.get(`${API_BASE}/${reportId}/content`)
    const statusResponse = await axios.get(`${API_BASE}/${reportId}/status`)

    console.log('内容响应:', contentResponse.data)
    console.log('状态响应:', statusResponse.data)

    if (contentResponse.data.success && statusResponse.data.success) {
      const contentData = contentResponse.data.data
      const statusData = statusResponse.data.data

      currentReport.value = {
        id: reportId,
        report_id: statusData.report_id || reportId,
        start_date: statusData.start_date,
        end_date: statusData.end_date,
        type: statusData.report_type,
        stats: statusData.stats || {},
        has_pdf: statusData.has_pdf || false,
        status: statusData.status,
        created_at: statusData.generated_at || new Date().toISOString(),
        markdown: contentData.markdown || '',
        key_issues: contentData.key_issues || '',
        sentiment_analysis: contentData.sentiment_analysis || {}
      }

      console.log('当前报告设置完成:', currentReport.value)
    }
  } catch (error) {
    console.error('加载报告详情失败:', error)
  }
}

// 预览报告
const previewReport = async (report) => {
  console.log('previewReport被调用，报告:', report)

  if (report.status !== 'completed') {
    showWarning('报告尚未完成，无法预览')
    return
  }

  showPreview.value = true
  previewReportData.value = report

  try {
    const response = await axios.get(`${API_BASE}/${report.id}/content`)

    if (response.data.success) {
      previewContent.value = marked.parse(response.data.data.markdown || '# 无内容')
    } else {
      previewContent.value = marked.parse('# 加载失败\n\n无法获取报告内容')
      showError('加载报告内容失败')
    }
  } catch (error) {
    console.error('预览报告失败:', error)
    previewContent.value = marked.parse('# 加载失败\n\n无法获取报告内容')
    showError('预览报告失败: ' + (error.message || '未知错误'))
  }
}

// 下载PDF
const downloadPDF = async (reportId) => {
  console.log('downloadPDF被调用，报告ID:', reportId)

  try {
    const response = await axios.get(
      `${API_BASE}/${reportId}/download`,
      { responseType: 'blob' }
    )

    const blob = new Blob([response.data], {
      type: 'application/pdf'
    })

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')

    a.href = url
    a.download = `报告_${reportId}.pdf`
    document.body.appendChild(a)
    a.click()

    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    showSuccess('报告下载成功')

  } catch (error) {
    console.error('下载失败:', error)
    showError(
      '下载失败: ' +
      (error.response?.data?.detail || error.message)
    )
  }
}


// 关闭预览
const closePreview = () => {
  showPreview.value = false
  previewContent.value = ''
  previewReportData.value = null
}

// 加载报告列表
const loadReportsList = async () => {
  try {
    console.log('加载报告列表...')
    const response = await axios.get(`${API_BASE}/list?limit=10`)

    console.log('报告列表响应:', response.data)

    if (response.data.success && Array.isArray(response.data.data)) {
      reports.value = response.data.data.map(report => ({
        id: report.id || report._id,
        report_id: report.report_id,
        start_date: report.start_date,
        end_date: report.end_date,
        type: report.report_type,
        stats: report.stats || {
          total: 0,
          risk_level: { high: 0, medium: 0, low: 0 },
          need_followup: 0
        },
        has_pdf: report.has_pdf || report.pdf_stored || false,
        status: report.status || 'unknown',
        created_at: report.generated_at || report.created_at || new Date().toISOString()
      }))

      console.log('处理后的报告列表:', reports.value)
    }
  } catch (error) {
    console.error('加载报告列表失败:', error)
    showError('加载报告列表失败')
  }
}

// 工具函数
const formatDate = (dateStr) => {
  if (!dateStr) return '未设置'
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  } catch {
    return dateStr
  }
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } catch {
    return ''
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}

const formatDateInput = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const getDateRangeDays = (start, end) => {
  if (!start || !end) return 0
  try {
    const startDate = new Date(start)
    const endDate = new Date(end)
    const diffTime = Math.abs(endDate - startDate)
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1 // +1 包含起止日期
  } catch {
    return 0
  }
}

const getStepStatusIcon = (status) => {
  switch (status) {
    case 'completed':
      return '✓'
    case 'processing':
      return '🔄'
    case 'pending':
      return '⏳'
    default:
      return '⏳'
  }
}

// 在组件销毁时清理轮询
onUnmounted(() => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
})

// 初始化
onMounted(() => {
  // 默认选择最近7天
  setQuickDate('7days')
  loadReportsList()

  // 添加一些调试信息
  console.log('组件挂载完成，当前时间:', new Date().toLocaleString('zh-CN'))
})
</script>

<style scoped>
/* 动画效果 */
@keyframes slide-in-right {
  from {
    transform: translateX(100%);
    opacity: 0;
  }

  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in-right {
  animation: slide-in-right 0.3s ease-out;
}

.prose h1 {
  font-size: 1.5rem;
  font-weight: bold;
  margin: 1rem 0;
  color: #111827;
}

.prose h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0.75rem 0;
  color: #1f2937;
}

.prose h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0.5rem 0;
  color: #374151;
}

.prose p {
  margin: 0.5rem 0;
  line-height: 1.6;
}

.prose ul,
.prose ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.prose li {
  margin: 0.25rem 0;
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0;
}

.prose th {
  background-color: #f9fafb;
  font-weight: 600;
  text-align: left;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
}

.prose td {
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
}

.prose code {
  background-color: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: 'Consolas', monospace;
  font-size: 0.875em;
}
</style>