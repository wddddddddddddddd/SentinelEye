import axios from 'axios'

// 根据环境变量动态设置 baseURL
const getBaseURL = () => {
  // 开发环境使用本地服务器
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888'
  }
  // 生产环境使用 /api 前缀（由 Nginx 代理）
  return '/api'
}

const apiClient = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000
})
// 获取最近的反馈 
export const getRecentFeedbacks = (limit = 5) => {
    return apiClient.get('/api/feedback/recent', {
        params: { limit }
    })
}

// 获取仪表盘统计数据
export const getDashboardStats = (limit = null) => {
    return apiClient.get('/api/dashboard/stats', {
        params: limit ? { limit } : {}
    })
}

// 新增：获取所有反馈
export const getAllFeedbacks = () => {
    return apiClient.get('/api/feedback/all')
}

// 新增：健康检查
export const healthCheck = () => {
    return apiClient.get('/health')
}

// 新增：获取趋势数据
export const getTrendData = (days = 7) => {
    return apiClient.get('/api/dashboard/stats', {
        params: { days }
    })
}

// 获取图表数据
export const getChartData = (days = 7) => {
    return apiClient.get('/api/dashboard/chart-data', {
        params: { 
            days: days,
        }
    })
}
