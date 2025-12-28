// api/analytics.js
import axios from 'axios'

// 根据环境变量动态设置 baseURL
const getBaseURL = () => {
  // 开发环境使用本地服务器
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888/api'
  }
  // 生产环境使用 /api 前缀（由 Nginx 代理）
  return '/api'
}

const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000
})

// 响应拦截器
apiClient.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error.response || error)
    return Promise.reject(error)
  }
)

// 分析数据 API
export const analyticsApi = {
  // 获取概览统计数据
  getOverviewStats(dateRange) {
    return apiClient.post('/analytics/overview', dateRange)
  },

  // 获取反馈类型分布
  getFeedbackTypeDistribution(dateRange) {
    return apiClient.post('/analytics/type-distribution', dateRange)
  },

  // 获取反馈趋势
  getFeedbackTrend(dateRange) {
    return apiClient.post('/analytics/trend', dateRange)
  },

  // 获取分类分析
  getCategoryAnalysis(dateRange) {
    return apiClient.post('/analytics/category', dateRange)
  },

  // 获取关键词分析
  getKeywordAnalysis(dateRange) {
    return apiClient.post('/analytics/keywords', dateRange)
  },

  // 获取所有数据
  getAllAnalytics(dateRange) {
    return apiClient.post('/analytics/all', dateRange)
  },

  // 生成周报
  generateWeeklyReport(dateRange) {
    return apiClient.post('/analytics/generate-report', dateRange, {
      responseType: 'blob'
    })
  }
}

// 工具函数：获取本周日期范围
export function getCurrentWeekRange() {
  const now = new Date()
  const dayOfWeek = now.getDay() // 0=周日, 1=周一, ...
  const start = new Date(now)
  
  // 计算本周一（如果今天是周日，则上周一）
  const diff = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  start.setDate(now.getDate() - diff)
  
  // 设置时间为00:00:00
  start.setHours(0, 0, 0, 0)
  
  // 结束日期是本周日（如果今天是周日，就是今天）
  const end = new Date(now)
  if (dayOfWeek !== 0) {
    end.setDate(now.getDate() + (7 - dayOfWeek))
  }
  end.setHours(23, 59, 59, 999)
  
  return {
    start_date: formatDate(start),
    end_date: formatDate(end),
    start_timestamp: start.getTime(),
    end_timestamp: end.getTime()
  }
}

// 格式化日期为 YYYY-MM-DD
export function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 格式化日期为中文显示
export function formatDateChinese(dateStr) {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${year}年${month}月${day}日`
}