import axios from 'axios'

// 根据环境设置 baseURL
const baseURL = import.meta.env.DEV 
    ? 'http://localhost:8888' 
    : '/api'

const apiClient = axios.create({
    baseURL: baseURL,
    timeout: 10000
})

// 获取最近的反馈 
export const getRecentFeedbacks = (limit = 5) => {
    return apiClient.get('/feedback/recent', {
        params: { limit }
    })
}

// 获取仪表盘统计数据
export const getDashboardStats = (limit = null) => {
    return apiClient.get('/dashboard/stats', {
        params: limit ? { limit } : {}
    })
}

// 新增：获取仪表盘摘要（包含趋势和分类）
export const getDashboardSummary = (limit = 100, recentLimit = 5) => {
    return apiClient.get('/dashboard/summary', {
        params: { 
            limit: limit,
            recent_limit: recentLimit 
        }
    })
}

// 新增：获取所有反馈
export const getAllFeedbacks = () => {
    return apiClient.get('/feedback/all')
}

// 新增：健康检查
export const healthCheck = () => {
    return apiClient.get('/health')
}

// 新增：获取趋势数据
export const getTrendData = (days = 7) => {
    return apiClient.get('/dashboard/stats', {
        params: { days }
    })
}

// 获取图表数据
export const getChartData = (days = 7, keywordDays = 3) => {
    return apiClient.get('/dashboard/chart-data', {
        params: { 
            days: days,
            keyword_days: keywordDays  // 新增参数
        }
    })
}

// 获取数据分析数据
export const getAnalyticsData = (days = 7) => {
    return apiClient.get('/analytics/data', {
        params: { days }
    })
}